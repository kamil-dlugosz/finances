from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import PROJECT_ROOT

logger = logging.getLogger(__name__)

CACHE_DIR = PROJECT_ROOT / ".cache"
FINGERPRINT_FILE = CACHE_DIR / "fingerprint.json"
EXPENSE_PARQUET = CACHE_DIR / "preprocessed.parquet"
INCOME_PARQUET = CACHE_DIR / "income.parquet"


def _count_csv_rows(path: Path) -> int:
    with open(path, encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)


CONFIG_DIR = PROJECT_ROOT / "config"
_CONFIG_FILES = ["hierarchy.yaml", "pipeline.yaml", "custom_tiers.yaml", "dashboard_queries.yaml"]


def compute_source_fingerprint(input_dir: Path) -> str:
    manifest: list[dict] = []
    for csv_file in sorted(input_dir.glob("*.csv")):
        manifest.append({
            "name": csv_file.name,
            "size_bytes": csv_file.stat().st_size,
            "row_count": _count_csv_rows(csv_file),
        })

    config_hashes: list[dict] = []
    for name in _CONFIG_FILES:
        cfg_path = CONFIG_DIR / name
        if cfg_path.exists():
            config_hashes.append({
                "name": name,
                "size_bytes": cfg_path.stat().st_size,
                "sha256": hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
            })

    payload = json.dumps(
        {"csv": manifest, "config": config_hashes}, sort_keys=True
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _read_stored_fingerprint() -> str | None:
    if not FINGERPRINT_FILE.exists():
        return None
    try:
        data = json.loads(FINGERPRINT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data.get("fingerprint")


def get_cache_metadata() -> dict | None:
    if not FINGERPRINT_FILE.exists():
        return None
    try:
        data = json.loads(FINGERPRINT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def is_cache_valid(input_dir: Path) -> bool:
    stored = _read_stored_fingerprint()
    if stored is None:
        return False
    if not EXPENSE_PARQUET.exists() or not INCOME_PARQUET.exists():
        return False
    current = compute_source_fingerprint(input_dir)
    return current == stored


def load_cache() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Loading preprocessed data from cache")
    try:
        expense_df = pd.read_parquet(EXPENSE_PARQUET)
        income_df = pd.read_parquet(INCOME_PARQUET)
    except Exception as exc:
        logger.error("Corrupt cache parquet — deleting cache: %s", exc)
        for f in (EXPENSE_PARQUET, INCOME_PARQUET, FINGERPRINT_FILE):
            if f.exists():
                f.unlink()
        raise RuntimeError("Cache corrupted and deleted — rerun to rebuild") from exc
    return expense_df, income_df


def save_cache(
    expense_df: pd.DataFrame,
    income_df: pd.DataFrame,
    input_dir: Path,
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if FINGERPRINT_FILE.exists():
        FINGERPRINT_FILE.unlink()

    tmp_paths: list[str] = []
    targets = [(expense_df, EXPENSE_PARQUET), (income_df, INCOME_PARQUET)]
    try:
        for df_to_save, _ in targets:
            fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, suffix=".parquet")
            os.close(fd)
            tmp_paths.append(tmp)
            df_to_save.to_parquet(tmp, index=False)

        for tmp, (_, target) in zip(tmp_paths, targets):
            os.replace(tmp, target)
        tmp_paths.clear()
    except BaseException:
        for tmp in tmp_paths:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise

    fingerprint = compute_source_fingerprint(input_dir)
    meta = {
        "fingerprint": fingerprint,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(input_dir),
        "file_count": len(list(input_dir.glob("*.csv"))),
        "expense_rows": len(expense_df),
        "income_rows": len(income_df),
    }
    FINGERPRINT_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("Cache saved with fingerprint %s", fingerprint[:12])
