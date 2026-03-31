from __future__ import annotations

import pytest
from plots.barplots import create_hierarchical_barplots


class TestBarplots:
    def test_returns_figure(self, preprocessed_expense_df):
        fig = create_hierarchical_barplots(preprocessed_expense_df)
        assert fig is not None
        assert len(fig.data) > 0

    def test_has_update_menus(self, preprocessed_expense_df):
        fig = create_hierarchical_barplots(preprocessed_expense_df)
        assert fig.layout.updatemenus is not None
        buttons = fig.layout.updatemenus[0].buttons
        assert len(buttons) == 4

    def test_legend_visible(self, preprocessed_expense_df):
        fig = create_hierarchical_barplots(preprocessed_expense_df)
        assert fig.layout.showlegend is True

    def test_traces_named_by_full_tier_path(self, preprocessed_expense_df):
        fig = create_hierarchical_barplots(preprocessed_expense_df)
        trace_names = {t.name for t in fig.data if t.name}
        for name in trace_names:
            assert " > " in name or name in preprocessed_expense_df["Tier1"].unique()
