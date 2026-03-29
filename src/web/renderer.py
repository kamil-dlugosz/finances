from __future__ import annotations

import json
import logging
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

from config import get_config
from etl.cache import get_cache_metadata

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).resolve().parent / "template.html"
LEGEND_JS_PATH = Path(__file__).resolve().parent / "legend.js"


def _fig_to_json(fig: go.Figure) -> str:
    return pio.to_json(fig)


def _build_cache_info() -> str:
    meta = get_cache_metadata()
    if meta is None:
        return "No cache info available"
    ts = meta.get("timestamp", "unknown")
    fc = meta.get("file_count", "?")
    er = meta.get("expense_rows", "?")
    ir = meta.get("income_rows", "?")
    return f"Last computed: {ts} | {fc} source files | {er} expense rows | {ir} income rows"


def render_html(
    sunburst_frames_json: str,
    barplots_fig: go.Figure,
    income_fig: go.Figure,
    waterfall_fig: go.Figure,
    sql_plot_figs: list[go.Figure],
    waterfall_stats_json: str,
    output_path: Path | str = "dist/output.html",
) -> Path:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    legend_js = LEGEND_JS_PATH.read_text(encoding="utf-8")

    tier_tree_json = json.dumps(get_config().hierarchy.tiers)

    sql_plots_json = "[" + ",".join(_fig_to_json(f) for f in sql_plot_figs) + "]"

    def _safe_json(raw: str) -> str:
        return raw.replace("</", "<\\/")

    replacements = {
        "{{LEGEND_JS}}": legend_js,
        "{{SUNBURST_FRAMES_JSON}}": _safe_json(sunburst_frames_json),
        "{{BARPLOTS_JSON}}": _safe_json(_fig_to_json(barplots_fig)),
        "{{INCOME_JSON}}": _safe_json(_fig_to_json(income_fig)),
        "{{WATERFALL_JSON}}": _safe_json(_fig_to_json(waterfall_fig)),
        "{{SQL_PLOTS_JSON}}": _safe_json(sql_plots_json),
        "{{TIER_TREE_JSON}}": _safe_json(tier_tree_json),
        "{{WATERFALL_STATS_JSON}}": _safe_json(waterfall_stats_json),
        "{{CACHE_INFO}}": _build_cache_info(),
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    out = Path(output_path)
    out.write_text(html, encoding="utf-8")
    logger.info("Dashboard written to %s", out.resolve())
    return out
