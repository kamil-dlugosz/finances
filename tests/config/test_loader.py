from __future__ import annotations

import pytest
from config.models import TierTree, AppConfig
from config.loader import get_config, get_tier_tree, _load_yaml


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

    def test_path_unknown_leaf_raises_valueerror(self):
        tree = TierTree({"A": ["x"]})
        with pytest.raises(ValueError, match="not found"):
            tree.path("nonexistent")

    def test_tier_order_preserves_config_insertion(self):
        tree = TierTree({"B": {"D": ["f", "e"]}, "A": {"C": ["g"]}})
        assert tree.tier_order(1) == ["B", "A"]
        assert tree.tier_order(2) == ["D", "C"]
        assert tree.tier_order(3) == ["f", "e", "g"]

    def test_ordered_leaves(self):
        tree = TierTree({"B": {"D": ["f", "e"]}, "A": {"C": ["g"]}})
        assert tree.ordered_leaves == ["f", "e", "g"]

    def test_tier_order_real_config(self):
        tree = get_tier_tree()
        tier1 = tree.tier_order(1)
        assert len(tier1) >= 2
        assert tier1[0] == "Utrzymanie"


class TestAppConfig:
    def test_loads_successfully(self):
        config = get_config()
        assert isinstance(config, AppConfig)
        assert len(config.hierarchy.dimensions) >= 1
        assert config.preprocessing_columns.amount_column == "Amount"


class TestLoadYaml:
    def test_missing_file_raises_runtime(self, tmp_path):
        with pytest.raises(RuntimeError, match="not found"):
            _load_yaml(tmp_path / "nonexistent.yaml")

    def test_empty_file_raises_runtime(self, tmp_path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(RuntimeError, match="empty"):
            _load_yaml(empty)

    def test_invalid_yaml_raises_runtime(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(":\n  - [invalid yaml\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="Failed to parse"):
            _load_yaml(bad)

    def test_valid_yaml_loads(self, tmp_path):
        good = tmp_path / "good.yaml"
        good.write_text("key: value\n", encoding="utf-8")
        result = _load_yaml(good)
        assert result == {"key": "value"}
