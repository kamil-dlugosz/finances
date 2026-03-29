import pandas as pd
import hashlib
import numpy as np


def _anonymize_string(value: str, prefix: str) -> str:
    if pd.isna(value):
        return value
    h = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{h}"


def anonymize_transactions(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = df.copy()

    text_columns = [
        "Nadawca / Odbiorca",
        "Adres nadawcy / odbiorcy",
        "Rachunek źródłowy",
        "Rachunek docelowy",
        "Tytułem",
        "Numer referencyjny",
    ]

    for col in text_columns:
        df[col] = df[col].astype(str).apply(lambda x: _anonymize_string(x, col[:3]))

    amount_col = "Kwota operacji"
    values = (
        df[amount_col]
        .astype(str)
        .str.replace(r"\s+", "", regex=True)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    noise = rng.normal(loc=0, scale=0.5, size=len(df))
    df[amount_col] = (values + noise).round(2)

    df[amount_col] = df[amount_col].map(lambda x: f"{x:.2f}".replace(".", ","))

    return df


if __name__ == "__main__":
    anonymize_transactions(
        pd.read_csv('statements/bank/2025_1.csv', sep=';', encoding='utf-8')
    ).to_csv('statements/anonymized/2025_1.csv', sep=';', index=False)
