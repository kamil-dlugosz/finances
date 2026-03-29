from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

from config import get_config


class TestLoadAllCsvFiles:
    def test_loads_real_data(self):
        from etl.loading import load_all_csv_files
        if not get_config().paths.source_statements_path.exists():
            pytest.skip("No test data")
        df = load_all_csv_files(get_config().paths.source_statements_path)
        assert len(df) > 0
        assert "PostingDate" in df.columns
        assert "Amount" in df.columns
        assert df["Amount"].dtype == float
        assert (df["Amount"] > 0).all()

    def test_missing_dir_raises(self, tmp_path):
        from etl.loading import load_all_csv_files
        with pytest.raises(FileNotFoundError):
            load_all_csv_files(tmp_path / "nonexistent")


class TestLoadIncome:
    def test_loads_income(self):
        from etl.loading import load_income_from_csv_files
        if not get_config().paths.source_statements_path.exists():
            pytest.skip("No test data")
        df = load_income_from_csv_files(get_config().paths.source_statements_path)
        assert len(df) > 0
        if len(df) > 0:
            assert "Amount" in df.columns
            assert (df["Amount"] > 0).all()


class TestLoadAllFromDir:
    def test_single_parse_split(self):
        from etl.loading import load_all_from_dir
        if not get_config().paths.source_statements_path.exists():
            pytest.skip("No test data")
        expense_df, income_df = load_all_from_dir(get_config().paths.source_statements_path)
        assert len(expense_df) > 0
        assert (expense_df["Amount"] > 0).all()
        if len(income_df) > 0:
            assert (income_df["Amount"] > 0).all()
