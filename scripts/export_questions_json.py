#!/usr/bin/env python3
"""Convert physics_qa_bank.yaml → web/questions.json for the review frontend."""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent


def first_sentence(text: str, max_len: int = 120) -> str:
    """Return the first sentence of text, capped at max_len characters."""
    text = text.strip().replace("\n", " ")
    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)
    if len(text) <= max_len:
        return text
    # Try to end at a sentence boundary within 1.5× max_len
    match = re.search(r"[.!?]", text[:int(max_len * 1.5)])
    if match:
        return text[: match.end()]
    return text[:max_len] + "…"


def main() -> None:
    src = ROOT / "data" / "physics_qa_bank.yaml"
    dst = ROOT / "web" / "questions.json"

    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        sys.exit(1)

    with open(src) as f:
        data = yaml.safe_load(f)

    questions = []
    for q in data["questions"]:
        questions.append(
            {
                "id": q["id"],
                "domain": q["domain"],
                "difficulty": q["difficulty"],
                "type": q["type"],
                "summary": first_sentence(q["question"]),
                "question": q["question"],
                "reference_answer": q["reference_answer"],
            }
        )

    dst.parent.mkdir(exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump({"questions": questions}, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(questions)} questions → {dst}")


if __name__ == "__main__":
    main()
