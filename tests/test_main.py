from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


STUB_SUNBURST_JSON = (
    '{"frames":{"50":{"ids":[],"parents":[],"labels":[],"values":[],"hovers":[],"colors":[],"names":[]}},'
    '"thresholds":[0,10,25,50,100,200,500],"max_depth":4,"dim_count":2,'
    '"leaf_tiers":[],"leaf_tier_paths":[],"tier1_colors":{}}'
)


class TestMain:
    def test_main_force_runs_pipeline(self, tmp_path, preprocessed_expense_df, sample_income_df):
        import plotly.graph_objects as go

        dummy_fig = go.Figure(go.Bar(x=["a"], y=[1]))
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        with (
            patch("sys.argv", ["main", "--force"]),
            patch("main.get_config") as mock_cfg,
            patch("main.load_all_from_dir", return_value=(preprocessed_expense_df, sample_income_df)),
            patch("main.preprocess", return_value=preprocessed_expense_df),
            patch("main.save_cache"),
            patch("main.sunburst_data_to_json", return_value=STUB_SUNBURST_JSON),
            patch("main.create_barplots_per_tier1", return_value={"T1": dummy_fig}),
            patch("main.create_income_barplot", return_value=dummy_fig),
            patch("main.create_sql_plots", return_value=[]),
            patch("main.waterfall_stats_to_json", return_value="[]"),
            patch("main.build_flowing_waterfall_data", return_value="{}"),
            patch("main.tier1_color_map", return_value={}),
            patch("main.render_html", return_value=dist_dir / "output.html") as mock_render,
        ):
            mock_cfg.return_value.paths.source_statements_path = tmp_path
            import main as main_mod
            main_mod.main()

        mock_render.assert_called_once()

    def test_main_cache_path(self, tmp_path, preprocessed_expense_df, sample_income_df):
        import plotly.graph_objects as go

        dummy_fig = go.Figure(go.Bar(x=["a"], y=[1]))
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        with (
            patch("sys.argv", ["main"]),
            patch("main.get_config") as mock_cfg,
            patch("main.is_cache_valid", return_value=True),
            patch("main.load_cache", return_value=(preprocessed_expense_df, sample_income_df)),
            patch("main.load_all_from_dir") as mock_load,
            patch("main.sunburst_data_to_json", return_value=STUB_SUNBURST_JSON),
            patch("main.create_barplots_per_tier1", return_value={"T1": dummy_fig}),
            patch("main.create_income_barplot", return_value=dummy_fig),
            patch("main.create_sql_plots", return_value=[]),
            patch("main.waterfall_stats_to_json", return_value="[]"),
            patch("main.build_flowing_waterfall_data", return_value="{}"),
            patch("main.tier1_color_map", return_value={}),
            patch("main.render_html", return_value=dist_dir / "output.html"),
        ):
            mock_cfg.return_value.paths.source_statements_path = tmp_path
            import main as main_mod
            main_mod.main()

        mock_load.assert_not_called()
