from __future__ import annotations

import re

import plotly.graph_objects as go
import pytest

from web.renderer import render_html


def _empty_fig() -> go.Figure:
    return go.Figure(go.Bar(x=["a"], y=[1]))


class TestRenderHtml:
    def test_produces_valid_html(self, preprocessed_expense_df, tmp_path):
        out = render_html(
            sunburst_fig=_empty_fig(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[],
            waterfall_stats_json="[]",
            expense_df=preprocessed_expense_df,
            output_path=tmp_path / "output.html",
        )
        assert out.exists()
        html = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_no_leftover_placeholders(self, preprocessed_expense_df, tmp_path):
        out = render_html(
            sunburst_fig=_empty_fig(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[],
            waterfall_stats_json="[]",
            expense_df=preprocessed_expense_df,
            output_path=tmp_path / "output.html",
        )
        html = out.read_text(encoding="utf-8")
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
        assert leftover == [], f"Unsubstituted placeholders: {leftover}"

    def test_sql_plots_injected(self, preprocessed_expense_df, tmp_path):
        fig = _empty_fig()
        out = render_html(
            sunburst_fig=_empty_fig(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[fig],
            waterfall_stats_json="[]",
            expense_df=preprocessed_expense_df,
            output_path=tmp_path / "output.html",
        )
        html = out.read_text(encoding="utf-8")
        assert '"data"' in html

    def test_uses_json_script_tags(self, preprocessed_expense_df, tmp_path):
        out = render_html(
            sunburst_fig=_empty_fig(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[],
            waterfall_stats_json="[]",
            expense_df=preprocessed_expense_df,
            output_path=tmp_path / "output.html",
        )
        html = out.read_text(encoding="utf-8")
        assert 'type="application/json"' in html
        assert "data-sunburst" in html
