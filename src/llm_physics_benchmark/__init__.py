"""
llm-physics-benchmark
=====================
Benchmark local LLMs via Ollama on expert-level particle physics questions.

Measures speed (tokens/sec, TTFT) and quality (LLM-judge scoring).
"""

__version__ = "0.1.0"
__all__ = ["OllamaClient", "run_benchmark", "judge_response"]

from llm_physics_benchmark.client import OllamaClient
from llm_physics_benchmark.judge import judge_response
from llm_physics_benchmark.runner import run_benchmark
