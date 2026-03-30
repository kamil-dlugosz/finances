from __future__ import annotations

import json

import pytest
from plots.sunburst import _build_sunburst_data, create_transaction_sunburst, sunburst_data_to_json


class TestSunburstData:
    def test_node_ids_unique(self, preprocessed_expense_df):
        data = _build_sunburst_data(preprocessed_expense_df, aggregation_threshold=0)
        assert len(data["ids"]) == len(set(data["ids"]))

    def test_all_lists_same_length(self, preprocessed_expense_df):
        data = _build_sunburst_data(preprocessed_expense_df, aggregation_threshold=0)
        n = len(data["ids"])
        assert len(data["parents"]) == n
        assert len(data["labels"]) == n
        assert len(data["values"]) == n
        assert len(data["hovers"]) == n
        assert len(data["colors"]) == n

    def test_transactions_have_parents(self, preprocessed_expense_df):
        data = _build_sunburst_data(preprocessed_expense_df, aggregation_threshold=0)
        id_set = set(data["ids"])
        for node_id, parent_id in zip(data["ids"], data["parents"]):
            if parent_id:
                assert parent_id in id_set, f"Parent '{parent_id}' of '{node_id}' not found"

    def test_aggregation_hides_small_transactions(self, preprocessed_expense_df):
        data_all = _build_sunburst_data(preprocessed_expense_df, aggregation_threshold=0)
        data_filtered = _build_sunburst_data(preprocessed_expense_df, aggregation_threshold=100)
        agg_nodes = [i for i in data_filtered["ids"] if "agg_hidden" in i]
        assert len(agg_nodes) > 0


class TestCreateSunburst:
    def test_returns_figure(self, preprocessed_expense_df):
        fig = create_transaction_sunburst(preprocessed_expense_df)
        assert fig is not None
        assert len(fig.data) > 0


class TestSunburstJson:
    def test_json_contains_dim_count(self, preprocessed_expense_df):
        raw = sunburst_data_to_json(preprocessed_expense_df)
        meta = json.loads(raw)
        assert "dim_count" in meta
        assert isinstance(meta["dim_count"], int)
        assert meta["dim_count"] >= 1

    def test_frames_contain_colors(self, preprocessed_expense_df):
        raw = sunburst_data_to_json(preprocessed_expense_df)
        meta = json.loads(raw)
        for key, frame in meta["frames"].items():
            assert "colors" in frame
            assert len(frame["colors"]) == len(frame["ids"])
