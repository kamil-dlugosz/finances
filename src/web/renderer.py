from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from config import get_config, PROJECT_ROOT
from etl.cache import get_cache_metadata

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).resolve().parent / "template.html"
LEGEND_JS_PATH = Path(__file__).resolve().parent / "legend.js"


def _fig_to_json(fig: go.Figure) -> str:
    return pio.to_json(fig)


def _build_dim_values_json(df: pd.DataFrame) -> str:
    dim_vals: dict[str, list[str]] = {}
    for dim_name in get_config().hierarchy.dimensions:
        col = f"Dim{dim_name}"
        if col in df.columns:
            dim_vals[dim_name] = sorted(df[col].dropna().unique().tolist())
    return json.dumps(dim_vals)


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
    sunburst_fig: go.Figure,
    barplots_fig: go.Figure,
    income_fig: go.Figure,
    waterfall_fig: go.Figure,
    sql_plot_figs: list[go.Figure],
    waterfall_stats_json: str,
    expense_df: pd.DataFrame,
    output_path: Path | str = "dist/output.html",
) -> Path:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    legend_js = LEGEND_JS_PATH.read_text(encoding="utf-8")

    tier_tree_json = json.dumps(get_config().hierarchy.tiers)
    dim_values_json = _build_dim_values_json(expense_df)

    sql_plots_json = "[" + ",".join(_fig_to_json(f) for f in sql_plot_figs) + "]"

    replacements = {
        "{{LEGEND_JS}}": legend_js,
        "{{SUNBURST_JSON}}": _fig_to_json(sunburst_fig),
        "{{BARPLOTS_JSON}}": _fig_to_json(barplots_fig),
        "{{INCOME_JSON}}": _fig_to_json(income_fig),
        "{{WATERFALL_JSON}}": _fig_to_json(waterfall_fig),
        "{{SQL_PLOTS_JSON}}": sql_plots_json,
        "{{TIER_TREE_JSON}}": tier_tree_json,
        "{{DIM_VALUES_JSON}}": dim_values_json,
        "{{WATERFALL_STATS_JSON}}": waterfall_stats_json,
        "{{CACHE_INFO}}": _build_cache_info(),
    }

    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    out = Path(output_path)
    out.write_text(html, encoding="utf-8")
    logger.info("Dashboard written to %s", out.resolve())
    return out
