"""Basic unit tests (no Ollama connection required)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from llm_physics_benchmark.judge import judge_response
from llm_physics_benchmark.model_lists import CONSUMER_MODELS, HIGHEND_MODELS, TIER_MAP
from llm_physics_benchmark.models import JudgeScore, ModelResponse
from llm_physics_benchmark.runner import _build_summary

# ── model_lists ───────────────────────────────────────────────────────────────

def test_tier_map_keys():
    assert set(TIER_MAP.keys()) == {"consumer", "highend", "all"}


def test_all_tier_contains_both():
    assert set(TIER_MAP["all"]) == set(CONSUMER_MODELS + HIGHEND_MODELS)


def test_no_duplicates_within_tier():
    assert len(CONSUMER_MODELS) == len(set(CONSUMER_MODELS))
    assert len(HIGHEND_MODELS) == len(set(HIGHEND_MODELS))


# ── qa bank ───────────────────────────────────────────────────────────────────

def test_qa_bank_loads():
    import yaml
    qa_path = Path(__file__).parent.parent / "data" / "physics_qa_bank.yaml"
    assert qa_path.exists(), "physics_qa_bank.yaml not found in data/"
    with open(qa_path) as f:
        data = yaml.safe_load(f)
    assert "questions" in data
    assert len(data["questions"]) >= 1
    for q in data["questions"]:
        assert "id" in q
        assert "question" in q
        assert "reference_answer" in q


# ── models dataclasses ────────────────────────────────────────────────────────

def test_model_response_defaults():
    r = ModelResponse(
        model="test", question_id="q1", question="Q?", answer="A.",
        prompt_tokens=10, response_tokens=20, total_tokens=30,
        time_to_first_token_s=0.5, total_time_s=2.0, tokens_per_second=10.0,
    )
    assert r.error is None
    assert r.timestamp  # non-empty string


def test_judge_score_defaults():
    s = JudgeScore(
        model="test", question_id="q1", judge_model="judge",
        accuracy_score=8, completeness_score=7, clarity_score=9,
        technical_depth_score=7, overall_score=7.7, judge_reasoning="Good.",
    )
    assert s.error is None


# ── runner summary ────────────────────────────────────────────────────────────

def _make_resp(model: str, qid: str, tps: float, t: float) -> ModelResponse:
    return ModelResponse(
        model=model, question_id=qid, question="Q?", answer="A.",
        prompt_tokens=10, response_tokens=20, total_tokens=30,
        time_to_first_token_s=0.3, total_time_s=t, tokens_per_second=tps,
    )


def _make_score(model: str, qid: str, overall: float) -> JudgeScore:
    return JudgeScore(
        model=model, question_id=qid, judge_model="judge",
        accuracy_score=8, completeness_score=7, clarity_score=9,
        technical_depth_score=7, overall_score=overall, judge_reasoning="ok",
    )


def test_build_summary_averages():
    responses = [_make_resp("m1", "q1", 30.0, 5.0), _make_resp("m1", "q2", 50.0, 3.0)]
    scores = [_make_score("m1", "q1", 8.0), _make_score("m1", "q2", 6.0)]
    questions = [{"id": "q1"}, {"id": "q2"}]

    summary = _build_summary(responses, scores, ["m1"], questions)
    assert "m1" in summary["models"]
    m = summary["models"]["m1"]
    assert m["avg_tokens_per_second"] == 40.0
    assert m["avg_overall_score"] == 7.0


def test_build_summary_missing_model():
    summary = _build_summary([], [], ["ghost_model"], [{"id": "q1"}])
    assert "ghost_model" not in summary["models"]


# ── judge JSON parsing ────────────────────────────────────────────────────────

def test_judge_parses_valid_json():
    fake_resp = ModelResponse(
        model="judge", question_id="", question="", answer='{"accuracy":8,"completeness":7,"clarity":9,"depth":6,"reasoning":"Good answer."}',
        prompt_tokens=5, response_tokens=20, total_tokens=25,
        time_to_first_token_s=0.1, total_time_s=1.0, tokens_per_second=20.0,
    )
    mock_client = MagicMock()
    mock_client.generate.return_value = fake_resp

    score = judge_response(mock_client, "judge", "Q?", "Ref.", "Ans.", "model_a", "q1")
    assert score.accuracy_score == 8
    assert score.completeness_score == 7
    assert score.clarity_score == 9
    assert score.technical_depth_score == 6
    assert score.overall_score == pytest.approx(8 * 0.4 + 7 * 0.3 + 9 * 0.15 + 6 * 0.15, abs=0.01)
    assert score.error is None


def test_judge_handles_malformed_json():
    fake_resp = ModelResponse(
        model="judge", question_id="", question="", answer="Sorry, no JSON here.",
        prompt_tokens=5, response_tokens=5, total_tokens=10,
        time_to_first_token_s=0.1, total_time_s=0.5, tokens_per_second=10.0,
    )
    mock_client = MagicMock()
    mock_client.generate.return_value = fake_resp

    score = judge_response(mock_client, "judge", "Q?", "Ref.", "Ans.", "model_a", "q1")
    assert score.error is not None
    assert score.overall_score == 0.0
