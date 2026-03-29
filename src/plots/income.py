from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go

from config import get_config, get_tier_tree


def create_income_barplot(income_df: pd.DataFrame) -> go.Figure:
    date_col = get_config().preprocessing_columns.date_stamp_column
    amount_col = get_config().preprocessing_columns.amount_column

    df = income_df.copy()
    df["Period"] = df[date_col].dt.to_period("M").apply(lambda r: r.start_time.date())
    agg = df.groupby("Period")[amount_col].sum().reset_index().sort_values("Period")

    fig = go.Figure(go.Bar(
        x=agg["Period"].astype(str),
        y=agg[amount_col],
        name="Income",
    ))
    fig.update_layout(
        title="Income Over Time",
        xaxis_title="Period",
        yaxis_title="Amount (PLN)",
        margin=dict(t=50, l=40, r=20, b=40),
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
    x_labels = ["Income"]
    y_values = [total_income]
    text_vals = [f"{total_income:,.2f}"]

    for tier, amount in tier1_sums.items():
        measures.append("relative")
        x_labels.append(str(tier))
        y_values.append(-amount)
        text_vals.append(f"-{amount:,.2f}")

    remaining = total_income - tier1_sums.sum()
    measures.append("total")
    x_labels.append("Net")
    y_values.append(remaining)
    text_vals.append(f"{remaining:,.2f}")

    fig = go.Figure(go.Waterfall(
        measure=measures,
        x=x_labels,
        y=y_values,
        text=text_vals,
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
        title="Income vs Expenses Waterfall",
        yaxis_title="Amount (PLN)",
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
                "tier_path": " → ".join(path_parts),
                "avg_amount": round(float(row["mean"]), 2),
                "count": int(row["count"]),
                "total": round(float(row["sum"]), 2),
            })

    return stats


def waterfall_stats_to_json(expense_df: pd.DataFrame) -> str:
    return json.dumps(build_waterfall_stats(expense_df))
