from __future__ import annotations

import pytest
from plots.income import (
    create_income_barplot,
    create_waterfall,
    build_waterfall_stats,
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


class TestWaterfallStats:
    def test_stats_structure(self, preprocessed_expense_df):
        stats = build_waterfall_stats(preprocessed_expense_df)
        assert isinstance(stats, list)
        assert len(stats) > 0
        entry = stats[0]
        assert "tier_path" in entry
        assert "avg_amount" in entry
        assert "count" in entry
        assert "total" in entry

    def test_stats_values_positive(self, preprocessed_expense_df):
        stats = build_waterfall_stats(preprocessed_expense_df)
        for s in stats:
            assert s["avg_amount"] > 0
            assert s["count"] > 0
