from __future__ import annotations

import pandas as pd
import pytest

from etl.preprocessing import preprocess, POLISH_MONTHS


class TestPreprocess:
    def test_adds_dimension_columns(self, sample_expense_df):
        result = preprocess(sample_expense_df)
        assert "DimYear" in result.columns
        assert "DimMonth" in result.columns
        assert result["DimYear"].iloc[0] == "2025"

    def test_adds_tier_columns(self, sample_expense_df):
        result = preprocess(sample_expense_df)
        assert "Tier1" in result.columns
        assert "Tier2" in result.columns
        assert "Tier3" in result.columns
        assert result["Tier1"].iloc[0] == "Utrzymanie"

    def test_full_path_format(self, sample_expense_df):
        result = preprocess(sample_expense_df)
        assert "FullPath" in result.columns
        fp = result["FullPath"].iloc[0]
        assert "|" in fp
        parts = fp.split("|")
        assert len(parts) == 5  # DimYear | DimMonth | Tier1 | Tier2 | Tier3

    def test_transaction_label(self, sample_expense_df):
        result = preprocess(sample_expense_df)
        assert "TransactionLabel" in result.columns
        label = result["TransactionLabel"].iloc[0]
        assert "PLN" in label

    def test_transaction_hover(self, sample_expense_df):
        result = preprocess(sample_expense_df)
        assert "TransactionHover" in result.columns

    def test_unknown_expense_type_fallback(self, sample_expense_df):
        df = sample_expense_df.copy()
        df.loc[0, "ExpenseType"] = "UNKNOWN_TYPE"
        result = preprocess(df)
        assert result.loc[0, "Tier1"] == "Bez kategorii"

    def test_polish_month_names(self):
        assert POLISH_MONTHS[1] == "Styczeń"
        assert POLISH_MONTHS[12] == "Grudzień"
        assert len(POLISH_MONTHS) == 12
