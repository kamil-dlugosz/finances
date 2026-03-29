from __future__ import annotations

import pandas as pd
import pytest
from predictions.validator import validate_expense_types, ValidationReport


class TestValidator:
    def test_returns_report(self, preprocessed_expense_df):
        report = validate_expense_types(preprocessed_expense_df)
        assert hasattr(report, "suspects")
        assert isinstance(report.suspects, list)

    def test_summary_is_string(self, preprocessed_expense_df):
        report = validate_expense_types(preprocessed_expense_df)
        summary = report.summary()
        assert isinstance(summary, str)

    def test_no_suspects_for_consistent_data(self, preprocessed_expense_df):
        report = validate_expense_types(preprocessed_expense_df, similarity_threshold=0.0)
        assert isinstance(report, ValidationReport)

    def test_high_threshold_flags_suspects(self, preprocessed_expense_df):
        report = validate_expense_types(preprocessed_expense_df, similarity_threshold=1.0)
        if len(report.suspects) > 0:
            s = report.suspects[0]
            assert hasattr(s, "expense_type")
            assert hasattr(s, "parent_tier")
            assert hasattr(s, "avg_similarity")
            assert s.avg_similarity <= 1.0
