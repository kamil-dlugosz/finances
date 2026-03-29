from __future__ import annotations

import pytest
from predictions.validator import validate_expense_types


class TestValidator:
    def test_returns_report(self, preprocessed_expense_df):
        report = validate_expense_types(preprocessed_expense_df)
        assert hasattr(report, "suspects")
        assert isinstance(report.suspects, list)

    def test_summary_is_string(self, preprocessed_expense_df):
        report = validate_expense_types(preprocessed_expense_df)
        summary = report.summary()
        assert isinstance(summary, str)
