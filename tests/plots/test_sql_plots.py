from __future__ import annotations

import yaml
import pytest
from plots.sql_plots import create_sql_plots, _load_queries


class TestSqlPlots:
    def test_no_queries_returns_empty(self, preprocessed_expense_df, sample_income_df, tmp_path, monkeypatch):
        monkeypatch.setattr("plots.sql_plots.QUERIES_PATH", tmp_path / "nonexistent.yaml")
        figures = create_sql_plots(preprocessed_expense_df, sample_income_df)
        assert isinstance(figures, list)
        assert len(figures) == 0

    def test_load_queries_returns_list(self):
        queries = _load_queries()
        assert isinstance(queries, list)

    def test_create_sql_plots_from_temp_config(self, preprocessed_expense_df, sample_income_df, tmp_path, monkeypatch):
        query_path = tmp_path / "dashboard_queries.yaml"
        query_path.write_text(
            yaml.safe_dump({
                "dashboard_queries": [{
                    "name": "Suma wydatkow",
                    "description": "",
                    "sql": (
                        "SELECT strftime(date_trunc('{granularity}', PostingDate), '%Y-%m-%d') AS period, "
                        "SUM(Amount) AS total "
                        "FROM transactions "
                        "GROUP BY 1 "
                        "ORDER BY 1"
                    ),
                }],
            }, allow_unicode=True),
            encoding="utf-8",
        )
        monkeypatch.setattr("plots.sql_plots.QUERIES_PATH", query_path)

        figures = create_sql_plots(preprocessed_expense_df, sample_income_df)

        assert len(figures) == 1
        fig = figures[0]
        assert len(fig.data) == 4
        assert any(len(getattr(trace, "x", [])) > 0 for trace in fig.data)
