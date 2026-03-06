"""Load curated model lists from model_lists.toml."""

import tomllib
from pathlib import Path

_toml = Path(__file__).parent.parent.parent / "config" / "model_lists.toml"
with _toml.open("rb") as _f:
    _config = tomllib.load(_f)

CONSUMER_MODELS: list[str] = _config["tiers"]["consumer"]["models"]
HIGHEND_MODELS: list[str] = _config["tiers"]["highend"]["models"]
DEFAULT_JUDGE_MODEL: str = _config["judge"]["default"]

TIER_MAP: dict[str, list[str]] = {
    "consumer": CONSUMER_MODELS,
    "highend": HIGHEND_MODELS,
    "all": CONSUMER_MODELS + HIGHEND_MODELS,
}
