from __future__ import annotations

import pytest
from predictions.clustering import cluster_tier


class TestClustering:
    def test_same_seed_same_result(self, preprocessed_expense_df, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")
        r1 = cluster_tier(preprocessed_expense_df, "Utrzymanie", n_clusters=2, seed=42)
        r2 = cluster_tier(preprocessed_expense_df, "Utrzymanie", n_clusters=2, seed=42)
        assert r1.clusters == r2.clusters

    def test_returns_clusters(self, preprocessed_expense_df, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")
        result = cluster_tier(preprocessed_expense_df, "Utrzymanie", n_clusters=2, seed=42)
        assert len(result.clusters) == 2
        assert all("keywords" in c for c in result.clusters)
        assert all("size" in c for c in result.clusters)

    def test_empty_subset_returns_zero_clusters(self, preprocessed_expense_df, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")
        result = cluster_tier(preprocessed_expense_df, "NonexistentTier/Path", n_clusters=3, seed=42)
        assert result.n_clusters == 0
        assert result.clusters == []

    def test_fewer_rows_than_clusters(self, preprocessed_expense_df, tmp_path, monkeypatch):
        monkeypatch.setattr("predictions.cache.PRED_CACHE_DIR", tmp_path)
        monkeypatch.setattr("predictions.cache.PRED_FINGERPRINT", tmp_path / "fingerprint.json")
        result = cluster_tier(preprocessed_expense_df, "Utrzymanie/Zdrowie", n_clusters=100, seed=42)
        assert result.n_clusters <= len(preprocessed_expense_df)
        assert len(result.clusters) > 0
