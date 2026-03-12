import pandas as pd
from pathlib import Path

from config import (
    DATE_STAMP_COLUMN,
    CATEGORY_STRUCTURE, EXPENSE_TYPE_COLUMN
)


def _add_category_month_year_column(df: pd.DataFrame) -> pd.DataFrame:
    df['CategoryMonthYear'] = df[DATE_STAMP_COLUMN].dt.strftime('%m.%Y')
    return df


def _build_subcategory_lookup() -> dict:
    return {
        subcategory: (category, group)
        for group, categories in CATEGORY_STRUCTURE.items()
        for category, subcategories in categories.items()
        for subcategory in subcategories
    }


def _add_category_depth_columns(df: pd.DataFrame) -> pd.DataFrame:
    subcategory_lookup = _build_subcategory_lookup()

    df["Category1"] = df[EXPENSE_TYPE_COLUMN].map(lambda val: subcategory_lookup.get(val, (None, None))[1])
    df["Category2"] = df[EXPENSE_TYPE_COLUMN].map(lambda val: subcategory_lookup.get(val, (None, None))[0])
    df["Category3"] = df[EXPENSE_TYPE_COLUMN]

    return df


def _add_category_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = _add_category_month_year_column(df)
    df = _add_category_depth_columns(df)
    return df


def _add_label_column_a(row: pd.Series) -> str:
    return "xd"


def _add_label_column_b(row: pd.Series) -> str:
    return "xd"


def _add_label_column_c(row: pd.Series) -> str:
    return "xd"


def _add_label_column_d(row: pd.Series) -> str:
    return "xd"


def _add_label_column_e(row: pd.Series) -> str:
    return "xd"


def _add_label_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["LabelColA"] = df.apply(_add_label_column_a, axis=1)
    df["LabelColB"] = df.apply(_add_label_column_b, axis=1)
    df["LabelColC"] = df.apply(_add_label_column_c, axis=1)
    df["LabelColD"] = df.apply(_add_label_column_d, axis=1)
    df["LabelColE"] = df.apply(_add_label_column_e, axis=1)
    return df


def _add_hover_column_a(row: pd.Series) -> str:
    return "xd"


def _add_hover_column_b(row: pd.Series) -> str:
    return "xd"


def _add_hover_column_c(row: pd.Series) -> str:
    return "xd"


def _add_hover_column_d(row: pd.Series) -> str:
    return "xd"


def _add_hover_column_e(row: pd.Series) -> str:
    return "xd"


def _add_hover_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["HoverColA"] = df.apply(_add_hover_column_a, axis=1)
    df["HoverColB"] = df.apply(_add_hover_column_b, axis=1)
    df["HoverColC"] = df.apply(_add_hover_column_c, axis=1)
    df["HoverColD"] = df.apply(_add_hover_column_d, axis=1)
    df["HoverColE"] = df.apply(_add_hover_column_e, axis=1)
    return df


def _split_and_save_by_month(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    df = df.sort_values(
        by=[DATE_STAMP_COLUMN]
    ).reset_index(drop=True)

    for month_period, month_df in df.groupby("CategoryMonthYear"):
        output_file = output_dir / f"{month_period}.csv"
        month_df.to_csv(output_file, sep=";")


def preprocess_and_save(df: pd.DataFrame, output_dir: Path) -> None:
    df = _add_category_columns(df)
    df = _add_label_columns(df)
    df = _add_hover_columns(df)
    
    _split_and_save_by_month(df, output_dir)
