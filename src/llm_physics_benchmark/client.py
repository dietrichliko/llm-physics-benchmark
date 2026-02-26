"""Ollama HTTP client with streaming and performance measurement."""

from __future__ import annotations

import json
import time
from typing import Optional

import requests

from llm_physics_benchmark.models import ModelResponse


class OllamaClient:
    """Thin wrapper around the Ollama REST API."""

    def __init__(self, host: str = "http://localhost:11434") -> None:
        self.host = host.rstrip("/")
        self.session = requests.Session()

    # ── Discovery ─────────────────────────────────────────────────────────────

    def list_models(self) -> list[str]:
        """Return names of models currently available in Ollama."""
        r = self.session.get(f"{self.host}/api/tags", timeout=10)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]

    def is_model_available(self, model: str) -> bool:
        available = self.list_models()
        return any(model in m or m in model for m in available)

    def pull_model(self, model: str) -> bool:
        """Pull *model* from the Ollama registry. Returns True on success."""
        r = self.session.post(
            f"{self.host}/api/pull",
            json={"name": model, "stream": False},
            timeout=600,
        )
        return r.status_code == 200

    # ── Inference ─────────────────────────────────────────────────────────────

    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        """
        Send *prompt* to Ollama /api/generate (streaming) and collect metrics.

        Returns a :class:`ModelResponse` with timing and token counts.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        answer_chunks: list[str] = []
        prompt_tokens = response_tokens = 0
        time_to_first_token: Optional[float] = None
        error: Optional[str] = None
        start = time.perf_counter()

        try:
            with self.session.post(
                f"{self.host}/api/generate",
                json=payload,
                stream=True,
                timeout=300,
            ) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines():
                    if not raw_line:
                        continue
                    chunk = json.loads(raw_line)
                    token_text: str = chunk.get("response", "")
                    if token_text and time_to_first_token is None:
                        time_to_first_token = time.perf_counter() - start
                    answer_chunks.append(token_text)
                    if chunk.get("done"):
                        prompt_tokens = chunk.get("prompt_eval_count", 0)
                        response_tokens = chunk.get("eval_count", 0)
                        break
        except requests.exceptions.RequestException as exc:
            error = str(exc)

        total_time = time.perf_counter() - start
        answer = "".join(answer_chunks)
        tps = response_tokens / total_time if total_time > 0 else 0.0
        ttft = time_to_first_token or total_time

        return ModelResponse(
            model=model,
            question_id="",
            question="",
            answer=answer,
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            total_tokens=prompt_tokens + response_tokens,
            time_to_first_token_s=round(ttft, 3),
            total_time_s=round(total_time, 3),
            tokens_per_second=round(tps, 2),
            error=error,
        )
