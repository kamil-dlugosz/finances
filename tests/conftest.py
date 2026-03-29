from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import pytest


@pytest.fixture
def sample_expense_df() -> pd.DataFrame:
    return pd.DataFrame({
        "PostingDate": pd.to_datetime([
            "2025-01-15", "2025-01-20", "2025-02-10",
            "2025-02-15", "2025-03-01", "2025-03-10",
            "2025-04-05", "2025-04-20", "2025-05-12",
            "2025-06-01",
        ]),
        "ValueDate": pd.to_datetime(["2025-01-15"] * 10),
        "Counterparty": [f"Vendor_{i}" for i in range(10)],
        "CounterpartyAddress": [f"Addr_{i}" for i in range(10)],
        "SourceAccount": ["SRC"] * 10,
        "TargetAccount": [f"TGT_{i}" for i in range(10)],
        "Title": [
            "Apteka", "Bilet autobusowy", "Czynsz za mieszkanie",
            "Zakupy Biedronka", "Kosmetyki drogeryjne", "Przelew wew",
            "Ubrania H&M", "Remont łazienki", "Restauracja",
            "Prezent urodzinowy",
        ],
        "Amount": [50.0, 15.0, 2000.0, 120.0, 45.0, 500.0, 200.0, 800.0, 90.0, 150.0],
        "Currency": ["PLN"] * 10,
        "ReferenceNumber": [f"REF{i}" for i in range(10)],
        "OperationType": ["TRANSAKCJA"] * 10,
        "ExpenseType": [
            "Lekarstwa", "Transport publiczny", "Czynsz",
            "Artykuły spożywcze", "Kosmetyki", "Przelew wewnętrzny",
            "Ubrania", "Naprawy i remonty", "Restauracje i kawiarnie",
            "Prezenty, upominki",
        ],
    })


@pytest.fixture
def sample_income_df() -> pd.DataFrame:
    return pd.DataFrame({
        "PostingDate": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
        "ValueDate": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
        "Counterparty": ["Employer"] * 3,
        "CounterpartyAddress": ["Addr"] * 3,
        "SourceAccount": ["EXT"] * 3,
        "TargetAccount": ["MY"] * 3,
        "Title": ["Wynagrodzenie"] * 3,
        "Amount": [8000.0, 8000.0, 8500.0],
        "Currency": ["PLN"] * 3,
        "ReferenceNumber": ["INC1", "INC2", "INC3"],
        "OperationType": ["PRZELEW"] * 3,
        "ExpenseType": ["Inne"] * 3,
    })


@pytest.fixture
def preprocessed_expense_df(sample_expense_df):
    from etl.preprocessing import preprocess
    return preprocess(sample_expense_df)
