from __future__ import annotations

import pytest
from plots.sql_plots import create_sql_plots, _load_queries


class TestSqlPlots:
    def test_no_queries_returns_empty(self, preprocessed_expense_df, sample_income_df):
        figures = create_sql_plots(preprocessed_expense_df, sample_income_df)
        assert isinstance(figures, list)
        assert len(figures) == 0

    def test_load_queries_returns_list(self):
        queries = _load_queries()
        assert isinstance(queries, list)
