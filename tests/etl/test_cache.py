from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path

from etl.cache import compute_source_fingerprint, save_cache, load_cache, is_cache_valid, CACHE_DIR


class TestFingerprint:
    def test_same_files_same_fingerprint(self, tmp_path):
        (tmp_path / "a.csv").write_text("h1;h2\n1;2\n")
        fp1 = compute_source_fingerprint(tmp_path)
        fp2 = compute_source_fingerprint(tmp_path)
        assert fp1 == fp2

    def test_different_content_different_fingerprint(self, tmp_path):
        (tmp_path / "a.csv").write_text("h1;h2\n1;2\n")
        fp1 = compute_source_fingerprint(tmp_path)
        (tmp_path / "a.csv").write_text("h1;h2\n1;2\n3;4\n")
        fp2 = compute_source_fingerprint(tmp_path)
        assert fp1 != fp2

    def test_added_file_changes_fingerprint(self, tmp_path):
        (tmp_path / "a.csv").write_text("h1;h2\n1;2\n")
        fp1 = compute_source_fingerprint(tmp_path)
        (tmp_path / "b.csv").write_text("h1;h2\n5;6\n")
        fp2 = compute_source_fingerprint(tmp_path)
        assert fp1 != fp2


class TestCacheRoundTrip:
    def test_save_and_load(self, tmp_path, sample_expense_df, sample_income_df, monkeypatch):
        monkeypatch.setattr("etl.cache.CACHE_DIR", tmp_path)
        monkeypatch.setattr("etl.cache.FINGERPRINT_FILE", tmp_path / "fingerprint.json")
        monkeypatch.setattr("etl.cache.EXPENSE_PARQUET", tmp_path / "preprocessed.parquet")
        monkeypatch.setattr("etl.cache.INCOME_PARQUET", tmp_path / "income.parquet")

        csv_dir = tmp_path / "source"
        csv_dir.mkdir()
        (csv_dir / "test.csv").write_text("h1\n1\n")

        save_cache(sample_expense_df, sample_income_df, csv_dir)
        loaded_exp, loaded_inc = load_cache()

        assert len(loaded_exp) == len(sample_expense_df)
        assert len(loaded_inc) == len(sample_income_df)
        assert is_cache_valid(csv_dir)
