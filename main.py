from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from config import get_config
from etl.loading import load_all_from_dir
from etl.preprocessing import preprocess
from etl.cache import is_cache_valid, load_cache, save_cache
from plots.sunburst import sunburst_data_to_json
from plots.barplots import create_hierarchical_barplots
from plots.income import create_income_barplot, create_waterfall, waterfall_stats_to_json, build_waterfall_source_data
from plots.sql_plots import create_sql_plots
from web.renderer import render_html

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the finances dashboard")
    parser.add_argument("--force", action="store_true", help="Force recompute, ignoring cache")
    args = parser.parse_args()

    source_dir = get_config().paths.source_statements_path

    if not args.force and is_cache_valid(source_dir):
        logger.info("Cache is valid — loading from cache")
        expense_df, income_df = load_cache()
    else:
        logger.info("Computing from source CSVs")
        raw_df, income_df = load_all_from_dir(source_dir)
        expense_df = preprocess(raw_df)
        save_cache(expense_df, income_df, source_dir)

    logger.info("Building figures")
    sunburst_frames_json = sunburst_data_to_json(expense_df)
    barplots_fig = create_hierarchical_barplots(expense_df)
    income_fig = create_income_barplot(income_df)
    waterfall_fig = create_waterfall(income_df, expense_df)
    sql_figs = create_sql_plots(expense_df, income_df)
    stats_json = waterfall_stats_to_json(expense_df)
    waterfall_source_json = build_waterfall_source_data(income_df, expense_df)

    dist_dir = Path(__file__).resolve().parent / "dist"
    dist_dir.mkdir(exist_ok=True)

    output = render_html(
        sunburst_frames_json=sunburst_frames_json,
        barplots_fig=barplots_fig,
        income_fig=income_fig,
        waterfall_fig=waterfall_fig,
        sql_plot_figs=sql_figs,
        waterfall_stats_json=stats_json,
        waterfall_source_json=waterfall_source_json,
        output_path=dist_dir / "output.html",
    )
    logger.info("Dashboard ready: %s", output.resolve())


if __name__ == "__main__":
    main()
