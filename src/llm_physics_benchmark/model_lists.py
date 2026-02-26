"""Load curated model lists from model_lists.toml."""

import importlib.resources
import tomllib

_toml = importlib.resources.files(__package__).joinpath("model_lists.toml")
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
