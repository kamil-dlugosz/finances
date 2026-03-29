from __future__ import annotations

import pytest
from predictions.clustering import cluster_tier


class TestClustering:
    def test_same_seed_same_result(self, preprocessed_expense_df):
        r1 = cluster_tier(preprocessed_expense_df, "Utrzymanie", n_clusters=2, seed=42)
        r2 = cluster_tier(preprocessed_expense_df, "Utrzymanie", n_clusters=2, seed=42)
        assert r1.clusters == r2.clusters

    def test_returns_clusters(self, preprocessed_expense_df):
        result = cluster_tier(preprocessed_expense_df, "Utrzymanie", n_clusters=2, seed=42)
        assert len(result.clusters) == 2
        assert all("keywords" in c for c in result.clusters)
        assert all("size" in c for c in result.clusters)
