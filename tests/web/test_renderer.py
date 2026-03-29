from __future__ import annotations

import json
import re

import plotly.graph_objects as go

from web.renderer import render_html


def _empty_fig() -> go.Figure:
    return go.Figure(go.Bar(x=["a"], y=[1]))


def _stub_frames_json() -> str:
    return json.dumps({
        "max_depth": 4,
        "thresholds": [0, 50],
        "frames": {
            "0": {"ids": ["a"], "parents": [""], "labels": ["A"], "values": [1], "hovers": [""]},
            "50": {"ids": ["a"], "parents": [""], "labels": ["A"], "values": [1], "hovers": [""]},
        },
    })


class TestRenderHtml:
    def test_produces_valid_html(self, tmp_path):
        out = render_html(
            sunburst_frames_json=_stub_frames_json(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[],
            waterfall_stats_json="[]",
            output_path=tmp_path / "output.html",
        )
        assert out.exists()
        html = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_no_leftover_placeholders(self, tmp_path):
        out = render_html(
            sunburst_frames_json=_stub_frames_json(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[],
            waterfall_stats_json="[]",
            output_path=tmp_path / "output.html",
        )
        html = out.read_text(encoding="utf-8")
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
        assert leftover == [], f"Unsubstituted placeholders: {leftover}"

    def test_sql_plots_injected(self, tmp_path):
        fig = _empty_fig()
        out = render_html(
            sunburst_frames_json=_stub_frames_json(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[fig],
            waterfall_stats_json="[]",
            output_path=tmp_path / "output.html",
        )
        html = out.read_text(encoding="utf-8")
        assert '"data"' in html

    def test_uses_json_script_tags(self, tmp_path):
        out = render_html(
            sunburst_frames_json=_stub_frames_json(),
            barplots_fig=_empty_fig(),
            income_fig=_empty_fig(),
            waterfall_fig=_empty_fig(),
            sql_plot_figs=[],
            waterfall_stats_json="[]",
            output_path=tmp_path / "output.html",
        )
        html = out.read_text(encoding="utf-8")
        assert 'type="application/json"' in html
        assert "data-sunburst-frames" in html
