from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from config import PROJECT_ROOT

PRED_CACHE_DIR = PROJECT_ROOT / ".cache" / "predictions"
PRED_FINGERPRINT = PRED_CACHE_DIR / "fingerprint.json"


def _preprocessed_fingerprint() -> str:
    parquet_path = PROJECT_ROOT / ".cache" / "preprocessed.parquet"
    if not parquet_path.exists():
        return ""
    stat = parquet_path.stat()
    payload = json.dumps({"mtime": stat.st_mtime, "size": stat.st_size}).encode()
    return hashlib.sha256(payload).hexdigest()


def is_prediction_cache_valid() -> bool:
    if not PRED_FINGERPRINT.exists():
        return False
    try:
        stored = json.loads(PRED_FINGERPRINT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(stored, dict):
        return False
    return stored.get("fingerprint") == _preprocessed_fingerprint()


def save_prediction_cache(result_name: str, data: str) -> Path:
    PRED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = PRED_CACHE_DIR / f"{result_name}.json"
    out.write_text(data, encoding="utf-8")

    meta = {
        "fingerprint": _preprocessed_fingerprint(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    PRED_FINGERPRINT.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out


def load_prediction_cache(result_name: str) -> str | None:
    path = PRED_CACHE_DIR / f"{result_name}.json"
    if not path.exists():
        return None
    if not is_prediction_cache_valid():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
