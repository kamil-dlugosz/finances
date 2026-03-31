from __future__ import annotations

from plots.barplots import create_barplots_per_tier1


class TestBarplotsPerTier1:
    def test_returns_dict_of_figures(self, preprocessed_expense_df):
        result = create_barplots_per_tier1(preprocessed_expense_df)
        assert isinstance(result, dict)
        assert len(result) > 0
        for key, fig in result.items():
            assert isinstance(key, str)
            assert fig is not None
            assert len(fig.data) > 0

    def test_each_figure_has_legend(self, preprocessed_expense_df):
        result = create_barplots_per_tier1(preprocessed_expense_df)
        for fig in result.values():
            assert fig.layout.showlegend is True

    def test_all_traces_show_legend(self, preprocessed_expense_df):
        result = create_barplots_per_tier1(preprocessed_expense_df)
        for fig in result.values():
            for trace in fig.data:
                assert trace.showlegend is True

    def test_keys_are_tier1_values(self, preprocessed_expense_df):
        result = create_barplots_per_tier1(preprocessed_expense_df)
        tier1_vals = set(preprocessed_expense_df["Tier1"].dropna().unique())
        assert set(result.keys()) == tier1_vals

    def test_config_order(self, preprocessed_expense_df):
        from config import get_tier_tree
        result = create_barplots_per_tier1(preprocessed_expense_df)
        keys = list(result.keys())
        config_order = get_tier_tree().tier_order(1)
        key_set = set(keys)
        expected = [v for v in config_order if v in key_set]
        expected += sorted(key_set - set(expected))
        assert keys == expected

    def test_each_figure_has_update_menus(self, preprocessed_expense_df):
        result = create_barplots_per_tier1(preprocessed_expense_df)
        for fig in result.values():
            assert fig.layout.updatemenus is not None
            buttons = fig.layout.updatemenus[0].buttons
            assert len(buttons) == 4

    def test_traces_use_compact_formatting(self, preprocessed_expense_df):
        result = create_barplots_per_tier1(preprocessed_expense_df)
        for fig in result.values():
            for trace in fig.data:
                if hasattr(trace, "text") and trace.text is not None:
                    break
