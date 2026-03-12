import pandas as pd
from pathlib import Path

from config import (
    FLOAT_TYPE_COLUMNS,
    DATE_TYPE_COLUMNS,
    COLUMN_NAME_MAPPING,
)


def _load_single_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep=";", decimal=",", dtype=str)

    for column in DATE_TYPE_COLUMNS:
        df[column] = pd.to_datetime(df[column], format="%d.%m.%Y")

    for column in FLOAT_TYPE_COLUMNS:
        df[column] = (
            df[column]
            .str.replace(",", ".", regex=False)
            .str.replace(" ", "", regex=False)
            .astype(float)
            * -1
        )
        df = df[df[column] > 0]

    return df


def load_all_csv_files(input_dir: Path) -> pd.DataFrame:
    dfs = []

    for csv_file in input_dir.glob("*.csv"):
        single_df = _load_single_csv(csv_file)
        dfs.append(single_df)

    combined_df = pd.concat(dfs, ignore_index=True).drop_duplicates()
    combined_df = combined_df.rename(columns=COLUMN_NAME_MAPPING)

    return combined_df
