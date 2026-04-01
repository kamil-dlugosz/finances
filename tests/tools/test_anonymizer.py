from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tools.anonymizer import _anonymize


class TestAnonymize:
    @pytest.fixture
    def sample_raw_df(self):
        return pd.DataFrame({
            "Data księgowania": ["15.01.2025"],
            "Data waluty": ["15.01.2025"],
            "Nadawca / Odbiorca": ["Jan Kowalski"],
            "Adres nadawcy / odbiorcy": ["ul. Testowa 1"],
            "Rachunek źródłowy": ["PL12345678"],
            "Rachunek docelowy": ["PL87654321"],
            "Tytułem": ["Zapłata za fakturę"],
            "Kwota operacji": ["-150,50"],
            "Waluta": ["PLN"],
            "Numer referencyjny": ["REF001"],
            "Typ operacji": ["PRZELEW"],
            "Kategoria": ["Artykuły spożywcze"],
        })

    def test_row_count_preserved(self, sample_raw_df):
        rng = np.random.default_rng(42)
        result = _anonymize(sample_raw_df, rng)
        assert len(result) == len(sample_raw_df)

    def test_string_columns_anonymized(self, sample_raw_df):
        rng = np.random.default_rng(42)
        result = _anonymize(sample_raw_df, rng)
        assert result["Nadawca / Odbiorca"].iloc[0] != "Jan Kowalski"
        assert result["Tytułem"].iloc[0] != "Zapłata za fakturę"
        assert result["Nadawca / Odbiorca"].iloc[0].startswith("Nad_")

    def test_dates_jittered(self, sample_raw_df):
        rng = np.random.default_rng(42)
        result = _anonymize(sample_raw_df, rng)
        date_val = result["Data księgowania"].iloc[0]
        parsed = pd.to_datetime(date_val, format="%d.%m.%Y")
        original = pd.Timestamp("2025-01-15")
        assert abs((parsed - original).days) <= 5

    def test_amounts_differ(self, sample_raw_df):
        rng = np.random.default_rng(42)
        result = _anonymize(sample_raw_df, rng)
        assert result["Kwota operacji"].iloc[0] != "-150,50"
