from __future__ import annotations

import pytest
from config.models import TierTree, AppConfig
from config.loader import get_config, get_tier_tree


class TestTierTree:
    def test_basic_structure(self):
        tree = TierTree({"A": {"B": ["c", "d"]}, "E": {"F": ["g"]}})
        assert tree.tier_depth == 3
        assert tree.path("c") == ("A", "B", "c")
        assert tree.path("g") == ("E", "F", "g")

    def test_contains(self):
        tree = TierTree({"A": ["x", "y"]})
        assert tree.contains("x")
        assert not tree.contains("z")

    def test_duplicate_at_same_depth_raises(self):
        with pytest.raises(ValueError, match="Duplicate"):
            TierTree({"A": ["x"], "B": ["x"]})

    def test_inconsistent_depth_raises(self):
        with pytest.raises(ValueError, match="Inconsistent"):
            TierTree({"A": ["leaf"], "B": {"C": ["deep_leaf"]}})

    def test_real_config_tier_tree(self):
        tree = get_tier_tree()
        assert tree.tier_depth == 3
        assert tree.path("Lekarstwa") == ("Utrzymanie", "Zdrowie", "Lekarstwa")
        assert tree.contains("Bez kategorii")


class TestAppConfig:
    def test_loads_successfully(self):
        config = get_config()
        assert isinstance(config, AppConfig)
        assert len(config.hierarchy.dimensions) >= 1
        assert config.preprocessing_columns.amount_column == "Amount"
