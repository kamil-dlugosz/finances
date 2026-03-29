from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

import pandas as pd
import yaml

from config import get_config, get_tier_tree, PROJECT_ROOT

logger = logging.getLogger(__name__)

POLISH_MONTHS: dict[int, str] = {
    1: "Styczeń", 2: "Luty", 3: "Marzec", 4: "Kwiecień",
    5: "Maj", 6: "Czerwiec", 7: "Lipiec", 8: "Sierpień",
    9: "Wrzesień", 10: "Październik", 11: "Listopad", 12: "Grudzień",
}

_DIMENSION_BUILDERS: dict[str, Callable[[pd.DataFrame, str], pd.Series]] = {
    "Year": lambda df, col: df[col].dt.year.astype(str),
    "Month": lambda df, col: df[col].dt.month.map(POLISH_MONTHS),
    "Quarter": lambda df, col: "Q" + df[col].dt.quarter.astype(str),
    "Week": lambda df, col: df[col].dt.isocalendar().week.astype(str),
}

_FALLBACK_TIER = "Bez kategorii"


def _preprocessing_columns():
    return get_config().preprocessing_columns


def _dimensions():
    return get_config().hierarchy.dimensions


def _tier_tree():
    return get_tier_tree()


def _load_custom_tiers() -> list[dict]:
    path = PROJECT_ROOT / "config" / "custom_tiers.yaml"
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse %s: %s — skipping custom tiers", path, exc)
        return []
    return data.get("custom_tiers", [])


def _apply_custom_tiers(df: pd.DataFrame) -> pd.DataFrame:
    rules = _load_custom_tiers()
    if not rules:
        return df

    depth = _tier_tree().tier_depth
    title_col = "Title"
    counterparty_col = "Counterparty"

    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict) or "match" not in rule or "assign" not in rule:
            logger.warning("Skipping malformed custom tier rule at index %d", idx)
            continue
        match = rule["match"]
        assign = rule["assign"]
        keywords = [kw.lower() for kw in match.get("keywords", [])]
        if not keywords:
            continue

        tier_path = match.get("tier_path", "")
        tier_path_segments = tier_path.split("/") if tier_path else []

        scope_mask = pd.Series(True, index=df.index)
        for i, segment in enumerate(tier_path_segments):
            col_name = f"Tier{i + 1}"
            if col_name in df.columns:
                scope_mask &= df[col_name] == segment

        keyword_mask = pd.Series(False, index=df.index)
        for kw in keywords:
            if title_col in df.columns:
                keyword_mask |= df[title_col].str.lower().str.contains(kw, na=False, regex=False)
            if counterparty_col in df.columns:
                keyword_mask |= df[counterparty_col].str.lower().str.contains(kw, na=False, regex=False)

        mask = scope_mask & keyword_mask

        for d in range(1, depth + 1):
            col_name = f"Tier{d}"
            tier_key = f"tier_{d}"
            if tier_key in assign and col_name in df.columns:
                df.loc[mask, col_name] = assign[tier_key]

    return df


def _add_dimension_columns(df: pd.DataFrame) -> pd.DataFrame:
    date_col = _preprocessing_columns().date_stamp_column
    for dim_name in _dimensions():
        builder = _DIMENSION_BUILDERS.get(dim_name)
        if builder is None:
            logger.warning("Unknown dimension '%s' — skipping", dim_name)
            continue
        df[f"Dim{dim_name}"] = builder(df, date_col)
    return df


def _add_tier_columns(df: pd.DataFrame) -> pd.DataFrame:
    tree = _tier_tree()
    expense_col = _preprocessing_columns().expense_type_column
    depth = tree.tier_depth
    fallback_path = (_FALLBACK_TIER,) * depth

    df[expense_col] = df[expense_col].fillna(_FALLBACK_TIER).astype(str)

    def resolve(val: str) -> tuple[str, ...]:
        if tree.contains(val):
            return tree.path(val)
        logger.warning("ExpenseType '%s' not in tier tree — falling back to '%s'", val, _FALLBACK_TIER)
        return fallback_path[: depth - 1] + (val,)

    paths = df[expense_col].map(resolve)

    for d in range(1, depth + 1):
        df[f"Tier{d}"] = paths.map(lambda p, _d=d: p[_d - 1] if _d <= len(p) else None)

    return df


def _build_full_path(df: pd.DataFrame) -> pd.DataFrame:
    dim_cols = [f"Dim{d}" for d in _dimensions()]
    tier_cols = [f"Tier{d}" for d in range(1, _tier_tree().tier_depth + 1)]
    all_cols = dim_cols + tier_cols
    df["FullPath"] = df[all_cols].apply(lambda row: "|".join(row.astype(str)), axis=1)
    return df


def _add_transaction_label(df: pd.DataFrame) -> pd.DataFrame:
    amount_col = _preprocessing_columns().amount_column
    target = df.get("TargetAccount", pd.Series("", index=df.index)).fillna("")
    title = df.get("Title", pd.Series("", index=df.index)).fillna("")
    amount = df[amount_col].map(lambda a: f"{a:.2f}")
    df["TransactionLabel"] = target + " · " + title + " · " + amount + " PLN"
    return df


def _add_transaction_hover(df: pd.DataFrame) -> pd.DataFrame:
    from html import escape
    skip = {"TransactionLabel", "TransactionHover", "FullPath"}
    hover_cols = [c for c in df.columns if c not in skip]
    df["TransactionHover"] = df[hover_cols].apply(
        lambda row: "<br>".join(f"{c}: {escape(str(row[c]))}" for c in hover_cols),
        axis=1,
    )
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = _add_dimension_columns(df)
    df = _add_tier_columns(df)
    df = _apply_custom_tiers(df)
    df = _build_full_path(df)
    df = _add_transaction_label(df)
    df = _add_transaction_hover(df)
    return df
