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
        "dim_count": 2,
        "leaf_tiers": ["TestTier"],
        "leaf_tier_paths": [{"name": "TestTier", "path": "Root > TestTier"}],
        "tier1_colors": {"Root": "hsl(210,60%,50%)"},
        "thresholds": [0, 50],
        "frames": {
            "0": {"ids": ["a"], "parents": [""], "labels": ["A"], "names": ["A"], "values": [1], "hovers": [""], "colors": ["#ccc"]},
            "50": {"ids": ["a"], "parents": [""], "labels": ["A"], "names": ["A"], "values": [1], "hovers": [""], "colors": ["#ccc"]},
        },
    })


def _render_kwargs(tmp_path):
    return dict(
        sunburst_frames_json=_stub_frames_json(),
        barplots_dict={"TestGroup": _empty_fig()},
        income_fig=_empty_fig(),
        sql_plot_figs=[],
        waterfall_stats_json="[]",
        flowing_waterfall_json="{}",
        tier1_colors_json="{}",
        output_path=tmp_path / "output.html",
    )


class TestRenderHtml:
    def test_produces_valid_html(self, tmp_path):
        out = render_html(**_render_kwargs(tmp_path))
        assert out.exists()
        html = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_no_leftover_placeholders(self, tmp_path):
        out = render_html(**_render_kwargs(tmp_path))
        html = out.read_text(encoding="utf-8")
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
        assert leftover == [], f"Unsubstituted placeholders: {leftover}"

    def test_sql_plots_injected(self, tmp_path):
        kwargs = _render_kwargs(tmp_path)
        kwargs["sql_plot_figs"] = [_empty_fig()]
        out = render_html(**kwargs)
        html = out.read_text(encoding="utf-8")
        assert '"data"' in html

    def test_uses_json_script_tags(self, tmp_path):
        out = render_html(**_render_kwargs(tmp_path))
        html = out.read_text(encoding="utf-8")
        assert 'type="application/json"' in html
        assert "data-sunburst-frames" in html
