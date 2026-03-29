from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class TestMain:
    def test_main_force_runs_pipeline(self, tmp_path, preprocessed_expense_df, sample_income_df):
        """main() with --force should compute from source and write output."""
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
            patch("main.create_transaction_sunburst", return_value=dummy_fig),
            patch("main.create_hierarchical_barplots", return_value=dummy_fig),
            patch("main.create_income_barplot", return_value=dummy_fig),
            patch("main.create_waterfall", return_value=dummy_fig),
            patch("main.create_sql_plots", return_value=[]),
            patch("main.waterfall_stats_to_json", return_value="[]"),
            patch("main.render_html", return_value=dist_dir / "output.html") as mock_render,
        ):
            mock_cfg.return_value.paths.source_statements_path = tmp_path
            import main as main_mod
            main_mod.main()

        mock_render.assert_called_once()

    def test_main_cache_path(self, tmp_path, preprocessed_expense_df, sample_income_df):
        """main() without --force with valid cache should skip recompute."""
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
            patch("main.create_transaction_sunburst", return_value=dummy_fig),
            patch("main.create_hierarchical_barplots", return_value=dummy_fig),
            patch("main.create_income_barplot", return_value=dummy_fig),
            patch("main.create_waterfall", return_value=dummy_fig),
            patch("main.create_sql_plots", return_value=[]),
            patch("main.waterfall_stats_to_json", return_value="[]"),
            patch("main.render_html", return_value=dist_dir / "output.html"),
        ):
            mock_cfg.return_value.paths.source_statements_path = tmp_path
            import main as main_mod
            main_mod.main()

        mock_load.assert_not_called()
