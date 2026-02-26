"""Shared data structures."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field


@dataclass
class ModelResponse:
    model: str
    question_id: str
    question: str
    answer: str
    prompt_tokens: int
    response_tokens: int
    total_tokens: int
    time_to_first_token_s: float
    total_time_s: float
    tokens_per_second: float
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


@dataclass
class JudgeScore:
    model: str
    question_id: str
    judge_model: str
    accuracy_score: int  # 0-10
    completeness_score: int  # 0-10
    clarity_score: int  # 0-10
    technical_depth_score: int  # 0-10
    overall_score: float  # weighted average
    judge_reasoning: str
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
