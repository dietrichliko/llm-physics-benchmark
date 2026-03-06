"""Command-line interface — `physics-bench`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from rich.console import Console

from llm_physics_benchmark.client import OllamaClient
from llm_physics_benchmark.model_lists import DEFAULT_JUDGE_MODEL, TIER_MAP
from llm_physics_benchmark.runner import run_benchmark

console = Console()

_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_DEFAULT_QA = _DATA_DIR / "physics_qa_bank.yaml"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="physics-bench",
        description="Benchmark local LLMs on particle physics questions via Ollama.",
    )
    p.add_argument(
        "--tier",
        choices=list(TIER_MAP.keys()),
        default="consumer",
        help="Model tier to benchmark (default: consumer)",
    )
    p.add_argument(
        "--models",
        nargs="+",
        metavar="MODEL",
        help="Override tier: specify exact Ollama model names",
    )
    p.add_argument(
        "--judge",
        default=DEFAULT_JUDGE_MODEL,
        metavar="MODEL",
        help=f"Judge model for quality scoring (default: {DEFAULT_JUDGE_MODEL})",
    )
    p.add_argument(
        "--host",
        default="http://localhost:11434",
        metavar="URL",
        help="Ollama host URL (default: http://localhost:11434)",
    )
    p.add_argument(
        "--questions",
        default=str(_DEFAULT_QA),
        metavar="FILE",
        help=f"Path to Q&A YAML file (default: {_DEFAULT_QA})",
    )
    p.add_argument(
        "--output-dir",
        default="./results",
        metavar="DIR",
        help="Directory for result files (default: ./results)",
    )
    p.add_argument(
        "--max-tokens",
        type=int,
        default=1200,
        help="Maximum tokens per response (default: 1200)",
    )
    p.add_argument(
        "--pull",
        action="store_true",
        help="Auto-pull missing models from the Ollama registry",
    )
    p.add_argument(
        "--no-skip",
        action="store_true",
        help="Abort on missing models instead of skipping them",
    )
    p.add_argument(
        "--list-models",
        action="store_true",
        help="List models currently available in Ollama and exit",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    client = OllamaClient(host=args.host)

    if args.list_models:
        try:
            models = client.list_models()
            console.print("[bold]Models available in Ollama:[/bold]")
            for m in sorted(models):
                console.print(f"  {m}")
        except Exception as exc:
            console.print(f"[red]Cannot connect to Ollama at {args.host}: {exc}[/red]")
            sys.exit(1)
        return

    # Select models
    if args.models:
        models_to_test = args.models
    else:
        models_to_test = TIER_MAP[args.tier]

    # Load questions
    qa_path = Path(args.questions)
    if not qa_path.exists():
        console.print(f"[red]Questions file not found: {qa_path}[/red]")
        sys.exit(1)
    with open(qa_path) as f:
        questions = yaml.safe_load(f)["questions"]

    # Check Ollama connectivity
    try:
        client.list_models()
    except Exception as exc:
        console.print(f"[red]Cannot connect to Ollama at {args.host}: {exc}[/red]")
        console.print("Start Ollama with: [bold]ollama serve[/bold]")
        sys.exit(1)

    run_benchmark(
        models=models_to_test,
        questions=questions,
        client=client,
        judge_model=args.judge,
        output_dir=Path(args.output_dir),
        skip_unavailable=not args.no_skip,
        auto_pull=args.pull,
        max_tokens=args.max_tokens,
    )


if __name__ == "__main__":
    main()
