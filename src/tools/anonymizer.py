"""Anonymize raw bank statements from resources/statements/bank/ → resources/statements/anonymized/.

Run: python src/tools/anonymizer.py [--seed 42]
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_PREFIX_MAP: dict[str, str] = {
    "Nadawca / Odbiorca": "Nad",
    "Adres nadawcy / odbiorcy": "Adr",
    "Rachunek źródłowy": "Rac",
    "Rachunek docelowy": "Rac",
    "Tytułem": "Tyt",
    "Numer referencyjny": "Num",
    "Typ operacji": "Typ",
    "Kategoria": "Kat",
}


def _random_hex(rng: np.random.Generator, n: int = 10) -> str:
    return rng.bytes(n).hex()[:n]


def _anonymize(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    df = df.copy()

    csv_cfg = get_config().csv_loading
    date_cols = set(csv_cfg.date_type_columns)
    float_cols = set(csv_cfg.float_type_columns)
    all_source_cols = set(csv_cfg.column_name_mapping.keys())
    string_cols = all_source_cols - date_cols - float_cols

    for col in string_cols:
        if col not in df.columns:
            continue
        prefix = _PREFIX_MAP.get(col, col[:3])
        df[col] = df[col].apply(
            lambda v, _p=prefix, _r=rng: f"{_p}_{_random_hex(_r)}" if pd.notna(v) else v
        )

    for col in date_cols:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], format="%d.%m.%Y", errors="coerce")
        jitter_days = rng.integers(-5, 6, size=len(df))
        shifted = parsed + pd.to_timedelta(jitter_days, unit="D")
        df[col] = shifted.dt.strftime("%d.%m.%Y")

    for col in float_cols:
        if col not in df.columns:
            continue
        values = pd.to_numeric(
            df[col]
            .astype(str)
            .str.replace(r"\s+", "", regex=True)
            .str.replace(",", ".", regex=False),
            errors="coerce",
        )
        noise = rng.normal(loc=0, scale=0.5, size=len(df))
        anonymized = (values + noise).round(2)
        df[col] = anonymized.map(lambda x: f"{x:.2f}".replace(".", ","))

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Anonymize bank statements")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    paths = get_config().paths
    input_dir = paths.source_statements_raw_path
    output_dir = paths.source_statements_path

    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in %s", input_dir)
        return

    for csv_file in csv_files:
        logger.info("Anonymizing %s", csv_file.name)
        df = pd.read_csv(csv_file, sep=";", encoding="utf-8", dtype=str)
        df = _anonymize(df, rng)
        out_path = output_dir / csv_file.name
        df.to_csv(out_path, sep=";", index=False)
        logger.info("  → %s (%d rows)", out_path.name, len(df))

    logger.info("Done — %d files anonymized", len(csv_files))


if __name__ == "__main__":
    main()
