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

    def test_legend_hidden(self, preprocessed_expense_df):
        fig = create_hierarchical_barplots(preprocessed_expense_df)
        assert fig.layout.showlegend is False
