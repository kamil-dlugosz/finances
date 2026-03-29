from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from config.models import PROJECT_ROOT, AppConfig, TierTree

CONFIG_DIR = PROJECT_ROOT / "config"


def _load_yaml(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found: {path}")
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Failed to parse YAML file {path}: {exc}")
    if data is None:
        raise RuntimeError(f"Configuration file is empty: {path}")
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


@lru_cache(maxsize=1)
def _load_hierarchy() -> dict:
    return _load_yaml(CONFIG_DIR / "hierarchy.yaml")


@lru_cache(maxsize=1)
def _load_pipeline() -> dict:
    return _load_yaml(CONFIG_DIR / "pipeline.yaml")


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and return the full application config. Result is cached — call
    ``get_config.cache_clear()`` in tests to force reload."""
    pipeline = _load_pipeline()
    hierarchy = _load_hierarchy()
    return AppConfig(**pipeline, hierarchy=hierarchy)


@lru_cache(maxsize=1)
def get_tier_tree() -> TierTree:
    """Build and return the tier tree. Cached alongside config."""
    return TierTree(get_config().hierarchy.tiers)
