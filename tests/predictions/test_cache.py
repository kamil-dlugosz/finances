from __future__ import annotations

import pytest

from predictions.cache import (
    save_prediction_cache,
    load_prediction_cache,
    is_prediction_cache_valid,
    PRED_CACHE_DIR,
    PRED_FINGERPRINT,
)


class TestPredictionCache:
    def test_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")

        save_prediction_cache("test_result", '{"hello": "world"}')
        loaded = load_prediction_cache("test_result")
        assert loaded == '{"hello": "world"}'

    def test_load_nonexistent_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")

        assert load_prediction_cache("nonexistent") is None

    def test_invalid_fingerprint_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")

        save_prediction_cache("test_result", '{"data": 1}')
        monkeypatch.setattr("predictions.cache._preprocessed_fingerprint", lambda: "changed")
        assert load_prediction_cache("test_result") is None

    def test_cache_valid_with_matching_fingerprint(self, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")

        save_prediction_cache("result", '{}')
        assert is_prediction_cache_valid()
