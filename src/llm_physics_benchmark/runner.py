"""Benchmark runner — orchestrates model × question matrix."""

from __future__ import annotations

import dataclasses
import datetime
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from llm_physics_benchmark.client import OllamaClient
from llm_physics_benchmark.judge import judge_response
from llm_physics_benchmark.models import JudgeScore, ModelResponse

console = Console()

PHYSICS_SYSTEM = (
    "You are an expert in experimental particle physics, accelerator physics, "
    "and detector instrumentation. Give precise, technically accurate answers."
)


def run_benchmark(
    models: list[str],
    questions: list[dict],
    client: OllamaClient,
    judge_model: str,
    output_dir: Path,
    skip_unavailable: bool = True,
    auto_pull: bool = False,
    max_tokens: int = 1200,
) -> dict:
    """
    Run the full benchmark matrix (models × questions) and write result files.

    Returns the summary dict.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    responses_file = output_dir / f"responses_{run_id}.jsonl"
    scores_file = output_dir / f"scores_{run_id}.jsonl"
    summary_file = output_dir / f"summary_{run_id}.json"

    console.rule(f"[bold cyan]LLM Physics Benchmark — {run_id}")
    console.print(f"  Models   : {len(models)}")
    console.print(f"  Questions: {len(questions)}")
    console.print(f"  Judge    : {judge_model}")
    console.print(f"  Output   : {output_dir}\n")

    available = set(client.list_models())
    console.print(f"[dim]Ollama models available: {sorted(available)}[/dim]\n")

    all_responses: list[ModelResponse] = []
    all_scores: list[JudgeScore] = []

    for model in models:
        model_available = any(model in m or m in model for m in available)
        if not model_available:
            if auto_pull:
                console.print(f"[yellow]  Pulling {model} …[/yellow]")
                ok = client.pull_model(model)
                if not ok:
                    console.print(f"[red]  SKIP: could not pull {model}[/red]")
                    continue
            elif skip_unavailable:
                console.print(f"[dim]  SKIP: {model} not in Ollama (use --pull)[/dim]")
                continue

        console.rule(f"[bold blue]{model}")

        for q in questions:
            qid: str = q["id"]
            question_text: str = q["question"]
            reference: str = q["reference_answer"]

            console.print(
                f"  [cyan]{qid}[/cyan] [{q['domain']} / {q['difficulty']}] … ",
                end="",
            )

            resp = client.generate(
                model=model,
                prompt=question_text,
                system=PHYSICS_SYSTEM,
                temperature=0.1,
                max_tokens=max_tokens,
            )
            resp.question_id = qid
            resp.question = question_text

            if resp.error:
                console.print(f"[red]ERROR: {resp.error}[/red]")
            else:
                console.print(
                    f"[green]{resp.tokens_per_second:.1f} tok/s[/green] | "
                    f"{resp.total_time_s:.1f}s | "
                    f"{resp.response_tokens} tokens"
                )

            all_responses.append(resp)
            with open(responses_file, "a") as f:
                f.write(json.dumps(dataclasses.asdict(resp)) + "\n")

            # Judge
            if not resp.error and resp.answer.strip():
                console.print(f"    [dim]→ judging with {judge_model} …[/dim] ", end="")
                score = judge_response(
                    client, judge_model, question_text, reference,
                    resp.answer, model, qid,
                )
                if score.error:
                    console.print(f"[red]judge error: {score.error}[/red]")
                else:
                    console.print(
                        f"overall=[bold]{score.overall_score:.1f}[/bold]/10  "
                        f"(acc={score.accuracy_score} "
                        f"cmp={score.completeness_score} "
                        f"clr={score.clarity_score} "
                        f"dep={score.technical_depth_score})"
                    )
                all_scores.append(score)
                with open(scores_file, "a") as f:
                    f.write(json.dumps(dataclasses.asdict(score)) + "\n")

    summary = _build_summary(all_responses, all_scores, models, questions)
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    _print_summary(summary)
    console.print(f"\n[dim]Results in {output_dir}[/dim]")
    console.print(f"  responses : {responses_file.name}")
    console.print(f"  scores    : {scores_file.name}")
    console.print(f"  summary   : {summary_file.name}")
    return summary


# ── Private helpers ────────────────────────────────────────────────────────────

def _build_summary(
    responses: list[ModelResponse],
    scores: list[JudgeScore],
    models: list[str],
    questions: list[dict],
) -> dict:
    summary: dict = {"models": {}, "questions": [q["id"] for q in questions]}

    for model in models:
        mresps = [r for r in responses if r.model == model]
        mscores = [s for s in scores if s.model == model]
        if not mresps:
            continue

        valid_r = [r for r in mresps if not r.error]
        valid_s = [s for s in mscores if not s.error]

        def avg(vals: list[float]) -> float:
            return round(sum(vals) / len(vals), 2) if vals else 0.0

        summary["models"][model] = {
            "questions_attempted": len(mresps),
            "questions_succeeded": len(valid_r),
            "avg_tokens_per_second": avg([r.tokens_per_second for r in valid_r]),
            "avg_total_time_s": avg([r.total_time_s for r in valid_r]),
            "avg_time_to_first_token_s": avg([r.time_to_first_token_s for r in valid_r]),
            "avg_overall_score": avg([s.overall_score for s in valid_s]),
            "avg_accuracy_score": avg([s.accuracy_score for s in valid_s]),
            "per_question": {
                qid: {
                    "tokens_per_second": next(
                        (r.tokens_per_second for r in mresps if r.question_id == qid and not r.error), None
                    ),
                    "total_time_s": next(
                        (r.total_time_s for r in mresps if r.question_id == qid and not r.error), None
                    ),
                    "overall_score": next(
                        (s.overall_score for s in mscores if s.question_id == qid and not s.error), None
                    ),
                }
                for qid in [q["id"] for q in questions]
            },
        }
    return summary


def _print_summary(summary: dict) -> None:
    table = Table(title="Benchmark Summary", show_header=True, header_style="bold magenta")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Score", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Tok/s", justify="right")
    table.add_column("Avg Time", justify="right")

    rows = sorted(
        summary["models"].items(),
        key=lambda x: x[1].get("avg_overall_score", 0),
        reverse=True,
    )
    for model, data in rows:
        score = data["avg_overall_score"]
        color = "green" if score >= 7 else "yellow" if score >= 5 else "red"
        table.add_row(
            model,
            f"[{color}]{score:.1f}/10[/{color}]",
            f"{data['avg_accuracy_score']:.1f}/10",
            f"{data['avg_tokens_per_second']:.1f}",
            f"{data['avg_total_time_s']:.1f}s",
        )
    console.print(table)
