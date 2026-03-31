from __future__ import annotations

import json

import pytest
from plots.income import (
    create_income_barplot,
    create_waterfall,
    build_waterfall_stats,
    build_flowing_waterfall_data,
)


class TestIncomeBarplot:
    def test_returns_figure(self, sample_income_df):
        fig = create_income_barplot(sample_income_df)
        assert fig is not None
        assert len(fig.data) > 0


class TestWaterfall:
    def test_returns_figure(self, sample_income_df, preprocessed_expense_df):
        fig = create_waterfall(sample_income_df, preprocessed_expense_df)
        assert fig is not None
        assert len(fig.data) > 0

    def test_no_dropdown(self, sample_income_df, preprocessed_expense_df):
        fig = create_waterfall(sample_income_df, preprocessed_expense_df)
        assert fig.layout.updatemenus is None or len(fig.layout.updatemenus) == 0


class TestWaterfallStats:
    def test_stats_structure(self, preprocessed_expense_df):
        stats = build_waterfall_stats(preprocessed_expense_df)
        assert isinstance(stats, list)
        assert len(stats) > 0
        entry = stats[0]
        assert "tier_path" in entry
        assert "tier_name" in entry
        assert "tier1" in entry
        assert "depth" in entry
        assert "avg_amount" in entry
        assert "count" in entry
        assert "total" in entry

    def test_stats_values_positive(self, preprocessed_expense_df):
        stats = build_waterfall_stats(preprocessed_expense_df)
        for s in stats:
            assert s["avg_amount"] >= 0
            assert s["count"] > 0

    def test_stats_sorted_by_path(self, preprocessed_expense_df):
        stats = build_waterfall_stats(preprocessed_expense_df)
        paths = [s["tier_path"] for s in stats]
        assert paths == sorted(paths)

    def test_stats_depth_matches_path(self, preprocessed_expense_df):
        stats = build_waterfall_stats(preprocessed_expense_df)
        for s in stats:
            parts = s["tier_path"].split(" \u2192 ")
            assert s["depth"] == len(parts)

    def test_stats_tier1_present(self, preprocessed_expense_df):
        stats = build_waterfall_stats(preprocessed_expense_df)
        for s in stats:
            assert s["tier1"] == s["tier_path"].split(" \u2192 ")[0]


class TestFlowingWaterfall:
    def test_returns_valid_json(self, sample_income_df, preprocessed_expense_df):
        raw = build_flowing_waterfall_data(sample_income_df, preprocessed_expense_df)
        data = json.loads(raw)
        assert "month_periods" in data
        assert "year_periods" in data
        assert "income_by_month" in data
        assert "income_by_year" in data
        assert "expense_by_tier1_month" in data
        assert "expense_by_tier1_year" in data

    def test_periods_sorted(self, sample_income_df, preprocessed_expense_df):
        raw = build_flowing_waterfall_data(sample_income_df, preprocessed_expense_df)
        data = json.loads(raw)
        assert data["month_periods"] == sorted(data["month_periods"])
        assert data["year_periods"] == sorted(data["year_periods"])
