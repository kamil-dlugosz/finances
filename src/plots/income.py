from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go

from config import get_config, get_tier_tree
from etl.loading import INCOME_MIN_AMOUNT
from plots.colors import compact_fmt


def _pln(val: float) -> str:
    """Format number as Polish locale: 1.234,56"""
    s = f"{val:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def create_income_barplot(income_df: pd.DataFrame) -> go.Figure:
    date_col = get_config().preprocessing_columns.date_stamp_column
    amount_col = get_config().preprocessing_columns.amount_column

    df = income_df.copy()
    df["Period"] = df[date_col].dt.to_period("M").apply(lambda r: r.start_time.date())

    source_col = "Counterparty" if "Counterparty" in df.columns else "Title"
    df["_source"] = df[source_col].fillna("Nieznane").astype(str)

    agg = df.groupby(["Period", "_source"])[amount_col].sum().reset_index()
    sources = sorted(agg["_source"].unique())

    fig = go.Figure()
    for src in sources:
        subset = agg[agg["_source"] == src].sort_values("Period")
        fig.add_trace(go.Bar(
            x=subset["Period"].astype(str),
            y=subset[amount_col],
            name=src,
            hovertemplate=f"{src}<br>%{{y:,.2f}} PLN<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        title=f"Przychody w czasie (wg \u017ar\u00f3d\u0142a, \u2265 {_pln(INCOME_MIN_AMOUNT)} PLN)",
        xaxis_title="Okres",
        yaxis_title="Kwota (PLN)",
        separators=", ",
        margin=dict(t=50, l=40, r=20, b=40),
        legend=dict(font=dict(size=10)),
    )
    return fig


def create_waterfall(
    income_df: pd.DataFrame,
    expense_df: pd.DataFrame,
) -> go.Figure:
    amount_col = get_config().preprocessing_columns.amount_column

    total_income = income_df[amount_col].sum()
    tier1_sums = expense_df.groupby("Tier1")[amount_col].sum().sort_values(ascending=False)

    measures = ["absolute"]
    x_labels = ["Przychody"]
    y_values = [total_income]
    text_vals = [f"<b>+{compact_fmt(total_income)}</b>"]

    running = total_income
    for tier, amount in tier1_sums.items():
        measures.append("relative")
        x_labels.append(str(tier))
        y_values.append(-amount)
        running -= amount
        text_vals.append(f"<b>-{compact_fmt(amount)}</b>")

    measures.append("total")
    x_labels.append("Netto")
    y_values.append(running)
    text_vals.append(f"<b>{compact_fmt(running)}</b>")

    fig = go.Figure(go.Waterfall(
        measure=measures,
        x=x_labels,
        y=y_values,
        text=text_vals,
        textposition="outside",
        textfont=dict(size=11),
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing=dict(marker=dict(color="hsl(130,55%,42%)")),
        decreasing=dict(marker=dict(color="hsl(0,60%,50%)")),
        totals=dict(marker=dict(color="#4a90d9")),
    ))

    fig.update_layout(
        title="Przychody vs Wydatki",
        yaxis_title="Kwota (PLN)",
        separators=", ",
        margin=dict(t=50, l=40, r=20, b=40),
    )
    return fig


def build_waterfall_stats(expense_df: pd.DataFrame) -> list[dict]:
    amount_col = get_config().preprocessing_columns.amount_column
    depth = get_tier_tree().tier_depth
    tier_cols = [f"Tier{d}" for d in range(1, depth + 1)]

    stats: list[dict] = []

    for level in range(1, depth + 1):
        group_cols = tier_cols[:level]
        agg = expense_df.groupby(group_cols)[amount_col].agg(["mean", "count", "sum"]).reset_index()

        for _, row in agg.iterrows():
            path_parts = [str(row[c]) for c in group_cols]
            stats.append({
                "tier_path": " \u2192 ".join(path_parts),
                "tier_name": path_parts[-1],
                "tier1": path_parts[0],
                "depth": level,
                "avg_amount": round(float(row["mean"]), 2),
                "count": int(row["count"]),
                "total": round(float(row["sum"]), 2),
            })

    order_by_depth: dict[int, dict[str, int]] = {}
    tree = get_tier_tree()
    for d in range(1, depth + 1):
        order_by_depth[d] = {v: i for i, v in enumerate(tree.tier_order(d))}

    def _sort_key(s: dict) -> tuple:
        parts = s["tier_path"].split(" \u2192 ")
        return tuple(order_by_depth.get(d + 1, {}).get(p, 999) for d, p in enumerate(parts))

    stats.sort(key=_sort_key)
    return stats


def waterfall_stats_to_json(expense_df: pd.DataFrame) -> str:
    return json.dumps(build_waterfall_stats(expense_df))


def build_waterfall_source_data(
    income_df: pd.DataFrame,
    expense_df: pd.DataFrame,
) -> str:
    """Embed monthly income/expense breakdowns for client-side waterfall recomputation."""
    amount_col = get_config().preprocessing_columns.amount_column
    date_col = get_config().preprocessing_columns.date_stamp_column

    inc = income_df.copy()
    inc["_month"] = inc[date_col].dt.to_period("M").astype(str)
    income_by_month: dict[str, float] = (
        inc.groupby("_month")[amount_col].sum().to_dict()
    )

    exp = expense_df.copy()
    exp["_month"] = exp[date_col].dt.to_period("M").astype(str)
    expense_by_tier1_month: dict[str, dict[str, float]] = {}
    for tier1, grp in exp.groupby("Tier1"):
        expense_by_tier1_month[str(tier1)] = grp.groupby("_month")[amount_col].sum().to_dict()

    all_months = sorted(set(income_by_month.keys()) | {m for d in expense_by_tier1_month.values() for m in d})

    return json.dumps({
        "months": all_months,
        "income_by_month": {k: round(v, 2) for k, v in income_by_month.items()},
        "expense_by_tier1_month": {
            t: {k: round(v, 2) for k, v in months.items()}
            for t, months in expense_by_tier1_month.items()
        },
    })


def build_flowing_waterfall_data(
    income_df: pd.DataFrame,
    expense_df: pd.DataFrame,
) -> str:
    """Build JSON for the flowing waterfall chart with monthly and yearly breakdowns."""
    amount_col = get_config().preprocessing_columns.amount_column
    date_col = get_config().preprocessing_columns.date_stamp_column

    inc = income_df.copy()
    exp = expense_df.copy()

    inc["_month"] = inc[date_col].dt.to_period("M").astype(str)
    inc["_year"] = inc[date_col].dt.year.astype(str)
    exp["_month"] = exp[date_col].dt.to_period("M").astype(str)
    exp["_year"] = exp[date_col].dt.year.astype(str)

    income_by_month = inc.groupby("_month")[amount_col].sum().to_dict()
    income_by_year = inc.groupby("_year")[amount_col].sum().to_dict()

    expense_by_t1_month: dict[str, dict[str, float]] = {}
    for tier1, grp in exp.groupby("Tier1"):
        expense_by_t1_month[str(tier1)] = {
            k: round(v, 2) for k, v in grp.groupby("_month")[amount_col].sum().to_dict().items()
        }

    expense_by_t1_year: dict[str, dict[str, float]] = {}
    for tier1, grp in exp.groupby("Tier1"):
        expense_by_t1_year[str(tier1)] = {
            k: round(v, 2) for k, v in grp.groupby("_year")[amount_col].sum().to_dict().items()
        }

    all_months = sorted(
        set(income_by_month.keys()) |
        {m for d in expense_by_t1_month.values() for m in d}
    )
    all_years = sorted(
        set(income_by_year.keys()) |
        {y for d in expense_by_t1_year.values() for y in d}
    )

    tree = get_tier_tree()
    config_tier1 = tree.tier_order(1)
    present_tier1 = set(expense_by_t1_month.keys()) | set(expense_by_t1_year.keys())
    tier1_order = [v for v in config_tier1 if v in present_tier1]
    for v in sorted(present_tier1 - set(tier1_order)):
        tier1_order.append(v)

    leaf_col = f"Tier{tree.tier_depth}"
    expense_by_leaf_month: dict[str, dict[str, float]] = {}
    for leaf, grp in exp.groupby(leaf_col):
        expense_by_leaf_month[str(leaf)] = {
            k: round(v, 2) for k, v in grp.groupby("_month")[amount_col].sum().to_dict().items()
        }
    expense_by_leaf_year: dict[str, dict[str, float]] = {}
    for leaf, grp in exp.groupby(leaf_col):
        expense_by_leaf_year[str(leaf)] = {
            k: round(v, 2) for k, v in grp.groupby("_year")[amount_col].sum().to_dict().items()
        }

    return json.dumps({
        "month_periods": all_months,
        "year_periods": all_years,
        "income_by_month": {k: round(v, 2) for k, v in income_by_month.items()},
        "income_by_year": {k: round(v, 2) for k, v in income_by_year.items()},
        "expense_by_tier1_month": expense_by_t1_month,
        "expense_by_tier1_year": expense_by_t1_year,
        "expense_by_leaf_month": expense_by_leaf_month,
        "expense_by_leaf_year": expense_by_leaf_year,
        "tier1_order": tier1_order,
    })
