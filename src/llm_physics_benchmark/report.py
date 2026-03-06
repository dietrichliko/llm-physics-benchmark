"""Generate an HTML report from benchmark result files — `physics-report`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def find_latest_run_id(results_dir: Path) -> str:
    summaries = sorted(results_dir.glob("summary_*.json"))
    return summaries[-1].stem.replace("summary_", "") if summaries else ""


def load_run(results_dir: Path, run_id: str) -> tuple[list, list, dict]:
    responses, scores, summary = [], [], {}
    for stem, target in (("responses", responses), ("scores", scores)):
        fp = results_dir / f"{stem}_{run_id}.jsonl"
        if fp.exists():
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        target.append(json.loads(line))  # type: ignore[attr-defined]
    sf = results_dir / f"summary_{run_id}.json"
    if sf.exists():
        with open(sf) as f:
            summary = json.load(f)
    return responses, scores, summary


def _color(score: float | None) -> str:
    if score is None:
        return "#64748b"
    if score >= 8:
        return "#22c55e"
    if score >= 6:
        return "#eab308"
    if score >= 4:
        return "#f97316"
    return "#ef4444"


def generate_html(responses: list, scores: list, summary: dict, run_id: str) -> str:
    resp_lut = {(r["model"], r["question_id"]): r for r in responses}
    score_lut = {(s["model"], s["question_id"]): s for s in scores}
    question_ids: list[str] = summary.get("questions", [])
    model_data: dict = summary.get("models", {})

    sorted_models = sorted(
        model_data.items(),
        key=lambda x: x[1].get("avg_overall_score", 0),
        reverse=True,
    )

    # ── Overview table ────────────────────────────────────────────────────────
    overview_rows = ""
    for rank, (model, data) in enumerate(sorted_models, 1):
        sc = data.get("avg_overall_score", 0)
        ac = data.get("avg_accuracy_score", 0)
        tps = data.get("avg_tokens_per_second", 0)
        t = data.get("avg_total_time_s", 0)
        ttft = data.get("avg_time_to_first_token_s", 0) * 1000
        c = _color(sc)
        overview_rows += (
            f"<tr>"
            f"<td class='rank'>#{rank}</td>"
            f"<td class='mono'>{model}</td>"
            f"<td style='color:{c};font-weight:700'>{sc:.1f}</td>"
            f"<td style='color:{_color(ac)}'>{ac:.1f}</td>"
            f"<td class='r'>{tps:.1f}</td>"
            f"<td class='r'>{t:.1f}s</td>"
            f"<td class='r'>{ttft:.0f}ms</td>"
            f"</tr>\n"
        )

    # ── Detail table ──────────────────────────────────────────────────────────
    detail_rows = ""
    for model, _ in sorted_models:
        for qid in question_ids:
            r = resp_lut.get((model, qid))
            s = score_lut.get((model, qid))

            answer = r["answer"] if r and r.get("answer") else "N/A"
            answer = answer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            reasoning = ""
            if s and s.get("judge_reasoning"):
                reasoning = (
                    s["judge_reasoning"]
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )

            ov = s["overall_score"] if s and not s.get("error") else None
            acc = s["accuracy_score"] if s and not s.get("error") else None
            cmp_ = s["completeness_score"] if s and not s.get("error") else None
            clr = s["clarity_score"] if s and not s.get("error") else None
            dep = s["technical_depth_score"] if s and not s.get("error") else None

            tps = f"{r['tokens_per_second']:.1f}" if r and not r.get("error") else "—"
            tt = f"{r['total_time_s']:.1f}s" if r and not r.get("error") else "—"
            ov_str = f"{ov:.1f}" if ov is not None else "N/A"

            detail_rows += (
                f"<tr>"
                f"<td class='mono sm'>{model}</td>"
                f"<td class='qid'>{qid}</td>"
                f"<td style='color:{_color(ov)};font-weight:700'>{ov_str}</td>"
                f"<td style='color:{_color(acc)}'>{acc if acc is not None else '—'}</td>"
                f"<td style='color:{_color(cmp_)}'>{cmp_ if cmp_ is not None else '—'}</td>"
                f"<td style='color:{_color(clr)}'>{clr if clr is not None else '—'}</td>"
                f"<td style='color:{_color(dep)}'>{dep if dep is not None else '—'}</td>"
                f"<td class='r'>{tps}</td>"
                f"<td class='r'>{tt}</td>"
                f"<td class='ans'>"
                f"<details><summary>Answer</summary><pre>{answer}</pre></details>"
                + (f"<div class='rsn'>{reasoning}</div>" if reasoning else "")
                + "</td>"
                "</tr>\n"
            )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LLM Physics Benchmark — {run_id}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:28px 32px}}
h1{{font-size:1.75rem;color:#f1f5f9;margin-bottom:4px}}
.meta{{color:#64748b;font-size:.85rem;margin-bottom:32px}}
h2{{font-size:1.05rem;color:#94a3b8;border-bottom:1px solid #1e293b;padding-bottom:6px;margin:36px 0 14px}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th{{background:#1e293b;color:#94a3b8;padding:9px 12px;text-align:left;position:sticky;top:0;z-index:1}}
td{{padding:8px 12px;border-bottom:1px solid #1e293b;vertical-align:top}}
tr:hover td{{background:#1e293b55}}
.rank{{color:#64748b;width:40px}}
.mono{{font-family:monospace;font-size:.78rem;color:#7dd3fc}}
.sm{{font-size:.74rem}}
.qid{{font-family:monospace;font-size:.75rem;color:#a78bfa}}
.r{{text-align:right;font-variant-numeric:tabular-nums}}
.ans{{max-width:480px}}
details summary{{cursor:pointer;color:#38bdf8;font-size:.8rem}}
pre{{white-space:pre-wrap;font-size:.72rem;background:#020617;padding:8px;border-radius:4px;color:#cbd5e1;margin-top:6px}}
.rsn{{margin-top:6px;font-size:.73rem;color:#94a3b8;font-style:italic}}
footer{{margin-top:48px;font-size:.75rem;color:#334155;text-align:center}}
</style>
</head>
<body>
<h1>⚛️ LLM Particle Physics Benchmark</h1>
<div class="meta">Run&nbsp;{run_id}&nbsp;&nbsp;·&nbsp;&nbsp;{len(sorted_models)}&nbsp;models&nbsp;&nbsp;·&nbsp;&nbsp;{len(question_ids)}&nbsp;questions</div>

<h2>Overall Rankings</h2>
<table>
<thead><tr><th>#</th><th>Model</th><th>Score /10</th><th>Accuracy</th><th>Tok/s</th><th>Avg Time</th><th>TTFT</th></tr></thead>
<tbody>{overview_rows}</tbody>
</table>

<h2>Per-Question Detail</h2>
<table>
<thead><tr><th>Model</th><th>Question</th><th>Overall</th><th>Acc</th><th>Cmp</th><th>Clr</th><th>Dep</th><th>Tok/s</th><th>Time</th><th>Answer / Reasoning</th></tr></thead>
<tbody>{detail_rows}</tbody>
</table>

<footer>Score weights: Accuracy 40 % · Completeness 30 % · Clarity 15 % · Depth 15 %</footer>
</body>
</html>"""


def main() -> None:
    p = argparse.ArgumentParser(
        prog="physics-report",
        description="Generate an HTML report from benchmark results.",
    )
    p.add_argument("--run-id", help="Specific run ID (timestamp string)")
    p.add_argument("--latest", action="store_true", help="Use the most recent run")
    p.add_argument(
        "--results-dir",
        default="./results",
        help="Results directory (default: ./results)",
    )
    args = p.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"ERROR: results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    run_id = args.run_id
    if not run_id or args.latest:
        run_id = find_latest_run_id(results_dir)
        if not run_id:
            print("No runs found.", file=sys.stderr)
            sys.exit(1)
        print(f"Using run: {run_id}")

    responses, scores, summary = load_run(results_dir, run_id)
    html = generate_html(responses, scores, summary, run_id)

    out = results_dir / f"report_{run_id}.html"
    out.write_text(html)
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
