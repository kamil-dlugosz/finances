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


def load_all_csv_files(input_dir: Path) -> pd.DataFrame:
    """Load expense transactions: negate amounts and keep positives (debits)."""
    cfg = _csv_loading()
    combined = _load_and_combine(input_dir)

    amount_col = cfg.column_name_mapping.get(cfg.float_type_columns[0], cfg.float_type_columns[0])
    combined[amount_col] = combined[amount_col] * -1
    combined = combined[combined[amount_col] > 0]

    return combined.reset_index(drop=True)


def load_income_from_csv_files(input_dir: Path) -> pd.DataFrame:
    """Load income transactions: keep rows where raw amount > 0 (credits)."""
    cfg = _csv_loading()
    combined = _load_and_combine(input_dir)

    amount_col = cfg.column_name_mapping.get(cfg.float_type_columns[0], cfg.float_type_columns[0])
    combined = combined[combined[amount_col] > 0]

    return combined.reset_index(drop=True)
