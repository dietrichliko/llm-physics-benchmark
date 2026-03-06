"""LLM-judge scoring of model answers against a reference expert answer."""

from __future__ import annotations

import json
import re

from llm_physics_benchmark.client import OllamaClient
from llm_physics_benchmark.models import JudgeScore

# Score weights (must sum to 1.0)
WEIGHTS = {
    "accuracy": 0.40,
    "completeness": 0.30,
    "clarity": 0.15,
    "depth": 0.15,
}

JUDGE_SYSTEM = """\
You are an expert in experimental particle physics evaluating LLM answers.
You will receive a question, a reference expert answer, and a model's answer.
Score the model answer on four dimensions (0-10 each):

1. ACCURACY     – Are factual claims correct? Penalise wrong numbers, formulae, names.
2. COMPLETENESS – Are the key concepts from the reference answer covered?
3. CLARITY      – Is the answer well-structured, concise, and readable?
4. DEPTH        – Is the technical depth appropriate for a physics expert?

Respond ONLY in valid JSON, no extra text, no markdown fences:
{
  "accuracy": <0-10>,
  "completeness": <0-10>,
  "clarity": <0-10>,
  "depth": <0-10>,
  "reasoning": "<max 2 sentences, under 60 words>"
}"""


def judge_response(
    client: OllamaClient,
    judge_model: str,
    question: str,
    reference_answer: str,
    model_answer: str,
    model_name: str,
    question_id: str,
    num_ctx: int = 8192,
    num_batch: int = 1024,
) -> JudgeScore:
    """Score *model_answer* against *reference_answer* using *judge_model*."""

    prompt = (
        f"QUESTION:\n{question}\n\n"
        f"REFERENCE EXPERT ANSWER:\n{reference_answer}\n\n"
        f"MODEL ANSWER TO EVALUATE:\n{model_answer}\n\n"
        "Score this model answer strictly against the reference."
    )

    resp = client.generate(
        model=judge_model,
        prompt=prompt,
        system=JUDGE_SYSTEM,
        temperature=0.0,
        max_tokens=256,
        num_ctx=num_ctx,
        num_batch=num_batch,
    )

    accuracy = completeness = clarity = depth = 0
    reasoning = ""
    error = resp.error

    if not error:
        raw = resp.answer.strip()
        json_match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if json_match:
            try:
                raw_json = json_match.group()
                # Fix invalid JSON escape sequences (e.g. LaTeX \( \) \text{} in reasoning)
                raw_json = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw_json)
                data = json.loads(raw_json)
                accuracy = max(0, min(10, int(data.get("accuracy", 0))))
                completeness = max(0, min(10, int(data.get("completeness", 0))))
                clarity = max(0, min(10, int(data.get("clarity", 0))))
                depth = max(0, min(10, int(data.get("depth", 0))))
                reasoning = str(data.get("reasoning", ""))
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                error = f"JSON parse error: {exc} | Raw: {raw[:300]}"
        else:
            error = f"No JSON found in judge response: {raw[:300]}"

    overall = round(
        accuracy * WEIGHTS["accuracy"]
        + completeness * WEIGHTS["completeness"]
        + clarity * WEIGHTS["clarity"]
        + depth * WEIGHTS["depth"],
        2,
    )

    return JudgeScore(
        model=model_name,
        question_id=question_id,
        judge_model=judge_model,
        accuracy_score=accuracy,
        completeness_score=completeness,
        clarity_score=clarity,
        technical_depth_score=depth,
        overall_score=overall,
        judge_reasoning=reasoning,
        error=error,
    )
