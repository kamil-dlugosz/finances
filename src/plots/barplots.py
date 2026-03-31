from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config import get_config, get_tier_tree
from plots.colors import compact_fmt


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


def create_barplots_per_tier1(df: pd.DataFrame) -> dict[str, go.Figure]:
    """Return one figure per Tier1 group, each with its own legend of leaf tiers."""
    amount_col = get_config().preprocessing_columns.amount_column
    depth = get_tier_tree().tier_depth
    group_col = "Tier1"
    stack_col = f"Tier{depth}"
    single_tier = (group_col == stack_col)

    tier_cols = [f"Tier{d}" for d in range(1, depth + 1)]
    path_lookup: dict[str, str] = {}
    display_lookup: dict[str, str] = {}
    for _, row in df.drop_duplicates(subset=tier_cols, keep="first").iterrows():
        leaf = str(row[stack_col])
        parts = [str(row[c]) for c in tier_cols]
        path_lookup[leaf] = " > ".join(parts)
        display_lookup[leaf] = " > ".join(parts[1:]) if len(parts) > 1 else parts[0]

    tree = get_tier_tree()
    config_tier1_order = tree.tier_order(1)
    present_tier1 = set(df[group_col].dropna().unique())
    group_vals = [v for v in config_tier1_order if v in present_tier1]
    for v in sorted(present_tier1 - set(group_vals)):
        group_vals.append(v)
    granularities = ["year", "quarter", "month", "week"]

    result: dict[str, go.Figure] = {}

    for g in group_vals:
        g_df = df[df[group_col] == g]
        fig = go.Figure()
        trace_ranges: dict[str, tuple[int, int]] = {}

        for gran in granularities:
            start_idx = len(fig.data)
            agg = _aggregate_by_time(g_df, gran, group_col, stack_col)

            if single_tier:
                subset = agg.sort_values("Period")
                display_name = display_lookup.get(g, g)
                fig.add_trace(go.Bar(
                    x=subset["PeriodLabel"],
                    y=subset[amount_col],
                    name=display_name,
                    showlegend=True,
                    visible=(gran == "month"),
                    hovertemplate=f"{display_name}<br>%{{y:,.2f}} PLN<extra></extra>",
                    text=subset[amount_col].apply(compact_fmt),
                    textposition="inside",
                    textangle=0,
                    textfont=dict(size=10),
                ))
            else:
                config_leaves = tree.ordered_leaves
                present_leaves = set(agg[stack_col].dropna().unique())
                stack_vals = [v for v in config_leaves if v in present_leaves]
                for v in sorted(present_leaves - set(stack_vals)):
                    stack_vals.append(v)
                for sv in stack_vals:
                    subset = agg[agg[stack_col] == sv].sort_values("Period")
                    display_name = display_lookup.get(str(sv), str(sv))
                    dn_parts = display_name.split(" > ")
                    leaf_label = dn_parts[-1]
                    group_label = " > ".join(dn_parts[:-1]) if len(dn_parts) > 1 else ""
                    trace_kwargs: dict = dict(
                        x=subset["PeriodLabel"],
                        y=subset[amount_col],
                        name=leaf_label,
                        showlegend=True,
                        visible=(gran == "month"),
                        hovertemplate=f"{display_name}<br>%{{y:,.2f}} PLN<extra></extra>",
                        text=subset[amount_col].apply(compact_fmt),
                        textposition="inside",
                        textangle=0,
                        textfont=dict(size=10),
                    )
                    if group_label:
                        trace_kwargs["legendgroup"] = group_label
                        trace_kwargs["legendgrouptitle"] = dict(
                            text=group_label, font=dict(size=11),
                        )
                    fig.add_trace(go.Bar(**trace_kwargs))

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
            showlegend=True,
            legend=dict(font=dict(size=10), tracegroupgap=6, groupclick="togglegroup"),
            title=dict(text=g, font=dict(size=14)),
            updatemenus=[{
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": 1.15,
                "buttons": buttons,
                "showactive": True,
                "visible": False,
            }],
            yaxis_title="Kwota (PLN)",
            separators=", ",
            margin=dict(t=50, l=40, r=20, b=40),
            height=350,
        )
        fig.update_xaxes(type="category", tickangle=-45)

        result[g] = fig

    return result
