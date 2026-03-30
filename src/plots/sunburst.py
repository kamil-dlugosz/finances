from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go

from config import get_config, get_tier_tree

_TIER1_PALETTE = [
    "hsl(210,60%,50%)", "hsl(30,70%,50%)", "hsl(130,50%,45%)",
    "hsl(0,60%,50%)", "hsl(270,50%,55%)", "hsl(50,70%,48%)",
    "hsl(180,50%,45%)", "hsl(330,55%,50%)",
]
_DIM_COLOR = "hsl(0,0%,78%)"
_TX_OPACITY = 0.45


def _pln(val: float) -> str:
    """Format number as Polish locale: 1.234,56"""
    s = f"{val:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def _build_sunburst_data(
    df: pd.DataFrame,
    aggregation_threshold: float = 0.0,
) -> dict[str, list]:
    cfg = get_config()
    tree = get_tier_tree()
    depth = tree.tier_depth
    dim_cols = [f"Dim{d}" for d in cfg.hierarchy.dimensions]
    tier_cols = [f"Tier{d}" for d in range(1, depth + 1)]
    amount_col = cfg.preprocessing_columns.amount_column
    all_path_cols = dim_cols + tier_cols
    dim_count = len(dim_cols)

    tier1_vals = sorted(df["Tier1"].dropna().unique())
    tier1_color_map = {v: _TIER1_PALETTE[i % len(_TIER1_PALETTE)] for i, v in enumerate(tier1_vals)}

    ids: list[str] = []
    parents: list[str] = []
    labels: list[str] = []
    values: list[float] = []
    hovers: list[str] = []
    colors: list[str] = []

    seen: set[str] = set()

    def _color_for(parts: list[str], is_tx: bool = False) -> str:
        tier_segs = parts[dim_count:]
        if not tier_segs:
            return _DIM_COLOR
        base = tier1_color_map.get(tier_segs[0], _DIM_COLOR)
        if is_tx:
            return base.replace(")", f",{_TX_OPACITY})").\
                replace("hsl(", "hsla(")
        tier_depth_here = len(tier_segs)
        lightness_bump = (tier_depth_here - 1) * 8
        h, s, l_part = base.split(",")
        l_val = int(l_part.replace("%)", ""))
        return f"{h},{s},{min(l_val + lightness_bump, 85)}%)"

    def _add_node(node_id: str, parent_id: str, label: str, value: float,
                  hover: str, color: str) -> None:
        if node_id in seen:
            return
        seen.add(node_id)
        ids.append(node_id)
        parents.append(parent_id)
        labels.append(label)
        values.append(value)
        hovers.append(hover)
        colors.append(color)

    sort_cols = []
    for dim_name in cfg.hierarchy.dimensions:
        sort_col = f"Dim{dim_name}_sort"
        if sort_col in df.columns:
            sort_cols.append(sort_col)

    agg = df.groupby(all_path_cols, sort=False)[amount_col].sum().reset_index()
    if sort_cols:
        sort_agg_cols = [c for c in sort_cols if c in df.columns]
        if sort_agg_cols:
            sort_keys = df.groupby(all_path_cols, sort=False)[sort_agg_cols].first().reset_index()
            agg = agg.merge(sort_keys, on=all_path_cols, how="left")
            agg = agg.sort_values(sort_agg_cols).reset_index(drop=True)

    for _, row in agg.iterrows():
        parts: list[str] = []
        for i, col in enumerate(all_path_cols):
            val = str(row[col])
            parts.append(val)
            node_id = "|".join(parts)
            parent_id = "|".join(parts[:-1]) if len(parts) > 1 else ""

            if node_id not in seen:
                if i < len(all_path_cols) - 1:
                    sub_mask = pd.Series(True, index=agg.index)
                    for j in range(i + 1):
                        sub_mask &= agg[all_path_cols[j]] == parts[j]
                    node_sum = agg.loc[sub_mask, amount_col].sum()
                else:
                    node_sum = row[amount_col]

                hover_path = " \u2192 ".join(parts)
                label_text = f"{val}<br>{_pln(node_sum)} PLN"
                _add_node(node_id, parent_id, label_text, node_sum,
                          hover_path, _color_for(parts))

    for full_path, group in df.groupby("FullPath", sort=False):
        parent_id = str(full_path)
        parent_parts = str(full_path).split("|")
        sorted_group = group.sort_values(amount_col, ascending=False)

        above = sorted_group[sorted_group[amount_col] >= aggregation_threshold]
        below = sorted_group[sorted_group[amount_col] < aggregation_threshold]

        for tx_i, (_, tx_row) in enumerate(above.iterrows()):
            tx_id = f"{parent_id}|tx_{tx_i}"
            target = tx_row.get("TargetAccount", "")
            title = tx_row.get("Title", "")
            amt = tx_row[amount_col]
            tx_label = f"{target}<br>{title}<br>{_pln(amt)} PLN"
            tx_hover = tx_row.get("TransactionHover", "")
            _add_node(tx_id, parent_id, tx_label, amt, tx_hover,
                      _color_for(parent_parts, is_tx=True))

        if len(below) > 0:
            agg_sum = below[amount_col].sum()
            agg_id = f"{parent_id}|agg_hidden"
            agg_label = f"<b>[{len(below)} zagregowanych]<br>{_pln(agg_sum)} PLN</b>"
            agg_hover = f"{len(below)} transakcji poni\u017cej progu {aggregation_threshold:.0f} PLN"
            _add_node(agg_id, parent_id, agg_label, agg_sum, agg_hover,
                      _color_for(parent_parts, is_tx=True))

    return {"ids": ids, "parents": parents, "labels": labels,
            "values": values, "hovers": hovers, "colors": colors}


def build_sunburst_frames(df: pd.DataFrame) -> dict[float, dict[str, list]]:
    thresholds = [0, 10, 25, 50, 100, 200, 500]
    return {t: _build_sunburst_data(df, t) for t in thresholds}


def create_transaction_sunburst(df: pd.DataFrame) -> go.Figure:
    """Create a static sunburst figure (useful for standalone usage/tests)."""
    max_depth = len(get_config().hierarchy.dimensions) + get_tier_tree().tier_depth
    default_data = _build_sunburst_data(df, aggregation_threshold=50)

    fig = go.Figure(go.Sunburst(
        ids=default_data["ids"],
        labels=default_data["labels"],
        parents=default_data["parents"],
        values=default_data["values"],
        hovertext=default_data["hovers"],
        hoverinfo="text",
        branchvalues="total",
        maxdepth=max_depth,
    ))
    fig.update_layout(margin=dict(t=40, l=20, r=20, b=20))
    return fig


def sunburst_data_to_json(df: pd.DataFrame) -> str:
    """Return JSON with all threshold frames + metadata for client-side rendering."""
    frames_data = build_sunburst_frames(df)
    cfg = get_config()
    dim_count = len(cfg.hierarchy.dimensions)
    max_depth = dim_count + get_tier_tree().tier_depth
    return json.dumps({
        "max_depth": max_depth,
        "dim_count": dim_count,
        "thresholds": sorted(frames_data.keys()),
        "frames": {str(int(k)): v for k, v in frames_data.items()},
    })
