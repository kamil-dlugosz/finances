from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import get_config, get_tier_tree


def _fmt_thousands(val: float) -> str:
    return f"{val:,.0f}".replace(",", ".")


def _aggregate_by_time(
    df: pd.DataFrame,
    granularity: str,
    group_col: str,
    stack_col: str,
) -> pd.DataFrame:
    date_col = get_config().preprocessing_columns.date_stamp_column
    amount_col = get_config().preprocessing_columns.amount_column

    df = df.copy()
    if granularity == "year":
        df["Period"] = df[date_col].dt.to_period("Y").apply(lambda r: r.start_time.date())
        df["PeriodLabel"] = df[date_col].dt.year.astype(str)
    elif granularity == "quarter":
        df["Period"] = df[date_col].dt.to_period("Q").apply(lambda r: r.start_time.date())
        df["PeriodLabel"] = df[date_col].dt.year.astype(str) + " Q" + df[date_col].dt.quarter.astype(str)
    elif granularity == "week":
        df["Period"] = df[date_col].dt.to_period("W").apply(lambda r: r.start_time.date())
        df["PeriodLabel"] = df["Period"].astype(str)
    elif granularity == "month":
        df["Period"] = df[date_col].dt.to_period("M").apply(lambda r: r.start_time.date())
        df["PeriodLabel"] = df[date_col].dt.to_period("M").astype(str)
    else:
        raise ValueError(f"Unknown granularity: {granularity}")

    group_cols = list(dict.fromkeys([group_col, stack_col]))
    grouped = df.groupby(group_cols + ["Period", "PeriodLabel"])[amount_col].sum().reset_index()
    return grouped


def create_hierarchical_barplots(df: pd.DataFrame) -> go.Figure:
    amount_col = get_config().preprocessing_columns.amount_column
    depth = get_tier_tree().tier_depth
    group_col = "Tier1"
    stack_col = f"Tier{min(2, depth)}"
    single_tier = (group_col == stack_col)

    group_vals = sorted(df[group_col].dropna().unique())
    n_cols = max(len(group_vals), 1)

    fig = make_subplots(
        rows=1,
        cols=n_cols,
        subplot_titles=group_vals,
        shared_yaxes=True,
    )

    granularities = ["year", "quarter", "month", "week"]
    trace_ranges: dict[str, tuple[int, int]] = {}

    for gran in granularities:
        start_idx = len(fig.data)
        agg = _aggregate_by_time(df, gran, group_col, stack_col)

        for col_idx, g in enumerate(group_vals, start=1):
            g_data = agg[agg[group_col] == g]

            if single_tier:
                subset = g_data.sort_values("Period")
                trace = go.Bar(
                    x=subset["PeriodLabel"],
                    y=subset[amount_col],
                    name=g,
                    legendgroup=g,
                    showlegend=False,
                    visible=(gran == "month"),
                    hovertemplate=f"{g}<br>%{{y:,.2f}} PLN<extra></extra>",
                    text=subset[amount_col].apply(_fmt_thousands),
                    textposition="inside",
                    textangle=0,
                    textfont=dict(size=10),
                )
                fig.add_trace(trace, row=1, col=col_idx)
            else:
                stack_vals = sorted(g_data[stack_col].dropna().unique())
                for sv in stack_vals:
                    subset = g_data[g_data[stack_col] == sv].sort_values("Period")
                    trace = go.Bar(
                        x=subset["PeriodLabel"],
                        y=subset[amount_col],
                        name=sv,
                        legendgroup=sv,
                        showlegend=False,
                        visible=(gran == "month"),
                        hovertemplate=f"{sv}<br>%{{y:,.2f}} PLN<extra></extra>",
                        text=subset[amount_col].apply(_fmt_thousands),
                        textposition="inside",
                        textangle=0,
                        textfont=dict(size=10),
                    )
                    fig.add_trace(trace, row=1, col=col_idx)

        trace_ranges[gran] = (start_idx, len(fig.data))

    total_traces = len(fig.data)
    buttons = []
    for gran in granularities:
        visibility = [False] * total_traces
        lo, hi = trace_ranges[gran]
        for j in range(lo, hi):
            visibility[j] = True
        buttons.append({
            "label": gran.capitalize(),
            "method": "update",
            "args": [{"visible": visibility}],
        })

    fig.update_layout(
        barmode="stack",
        showlegend=False,
        updatemenus=[{
            "type": "buttons",
            "direction": "left",
            "x": 0.0,
            "y": 1.15,
            "buttons": buttons,
            "showactive": True,
        }],
        yaxis_title="Kwota (PLN)",
        separators=", ",
        margin=dict(t=80, l=40, r=20, b=40),
        height=500,
    )
    fig.update_xaxes(type="category", tickangle=-45)

    return fig
