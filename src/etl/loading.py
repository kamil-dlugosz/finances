from __future__ import annotations

import pandas as pd
from pathlib import Path

from config import get_config


def _csv_loading():
    return get_config().csv_loading


def _load_single_csv(csv_path: Path) -> pd.DataFrame:
    cfg = _csv_loading()
    df = pd.read_csv(csv_path, sep=";", decimal=",", dtype=str, encoding="utf-8")

    for column in cfg.date_type_columns:
        df[column] = pd.to_datetime(df[column], format="%d.%m.%Y")

    for column in cfg.float_type_columns:
        df[column] = (
            df[column]
            .str.replace(",", ".", regex=False)
            .str.replace(r"\s+", "", regex=True)
            .astype(float)
        )

    return df


def _load_and_combine(input_dir: Path) -> pd.DataFrame:
    cfg = _csv_loading()
    dfs: list[pd.DataFrame] = []

    for csv_file in sorted(input_dir.glob("*.csv")):
        single_df = _load_single_csv(csv_file)
        dfs.append(single_df)

    if not dfs:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.rename(columns=cfg.column_name_mapping)

    ref_col = cfg.column_name_mapping.get("Numer referencyjny", "ReferenceNumber")
    if ref_col in combined.columns:
        combined = combined.drop_duplicates(subset=[ref_col])
    else:
        combined = combined.drop_duplicates()

    return combined


def _amount_col() -> str:
    cfg = _csv_loading()
    return cfg.column_name_mapping.get(cfg.float_type_columns[0], cfg.float_type_columns[0])


def load_all_csv_files(input_dir: Path) -> pd.DataFrame:
    """Load expense transactions: negate amounts and keep positives (debits)."""
    combined = _load_and_combine(input_dir)
    col = _amount_col()
    combined[col] = combined[col] * -1
    combined = combined[combined[col] > 0]
    return combined.reset_index(drop=True)


def load_income_from_csv_files(input_dir: Path) -> pd.DataFrame:
    """Load income transactions: keep rows where raw amount > 0 (credits)."""
    combined = _load_and_combine(input_dir)
    col = _amount_col()
    combined = combined[combined[col] > 0]
    return combined.reset_index(drop=True)


def load_all_from_dir(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load CSVs once and split into (expenses, income). More efficient than
    calling load_all_csv_files + load_income_from_csv_files separately."""
    combined = _load_and_combine(input_dir)
    col = _amount_col()

    income_df = combined[combined[col] > 0].reset_index(drop=True)

    expense_combined = combined.copy()
    expense_combined[col] = expense_combined[col] * -1
    expense_df = expense_combined[expense_combined[col] > 0].reset_index(drop=True)

    return expense_df, income_df
