from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go

from config import get_config, get_tier_tree


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

    ids: list[str] = []
    parents: list[str] = []
    labels: list[str] = []
    values: list[float] = []
    hovers: list[str] = []

    seen: set[str] = set()

    def _add_node(node_id: str, parent_id: str, label: str, value: float, hover: str) -> None:
        if node_id in seen:
            return
        seen.add(node_id)
        ids.append(node_id)
        parents.append(parent_id)
        labels.append(label)
        values.append(value)
        hovers.append(hover)

    agg = df.groupby(all_path_cols, sort=False)[amount_col].sum().reset_index()

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

                hover_path = " → ".join(parts)
                label_text = f"{val}<br>{node_sum:,.2f} PLN"
                _add_node(node_id, parent_id, label_text, node_sum, hover_path)

    for full_path, group in df.groupby("FullPath", sort=False):
        parent_id = str(full_path)
        sorted_group = group.sort_values(amount_col, ascending=False)

        above = sorted_group[sorted_group[amount_col] >= aggregation_threshold]
        below = sorted_group[sorted_group[amount_col] < aggregation_threshold]

        for idx, tx_row in above.iterrows():
            tx_id = f"{parent_id}|tx_{idx}"
            target = tx_row.get("TargetAccount", "")
            title = tx_row.get("Title", "")
            amt = tx_row[amount_col]
            tx_label = f"{target}<br>{title}<br>{amt:,.2f} PLN"
            tx_hover = tx_row.get("TransactionHover", "")
            _add_node(tx_id, parent_id, tx_label, amt, tx_hover)

        if len(below) > 0:
            agg_sum = below[amount_col].sum()
            agg_id = f"{parent_id}|agg_hidden"
            agg_label = f"<b>[{len(below)} aggregated]<br>{agg_sum:,.2f} PLN</b>"
            agg_hover = f"{len(below)} transactions under {aggregation_threshold:.0f} PLN threshold"
            _add_node(agg_id, parent_id, agg_label, agg_sum, agg_hover)

    return {"ids": ids, "parents": parents, "labels": labels, "values": values, "hovers": hovers}


def build_sunburst_frames(df: pd.DataFrame) -> dict[float, dict[str, list]]:
    thresholds = [0, 10, 25, 50, 100, 200, 500]
    return {t: _build_sunburst_data(df, t) for t in thresholds}


def create_transaction_sunburst(df: pd.DataFrame) -> go.Figure:
    max_depth = len(get_config().hierarchy.dimensions) + get_tier_tree().tier_depth

    frames_data = build_sunburst_frames(df)
    thresholds = sorted(frames_data.keys())

    default_data = frames_data[thresholds[0]]

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

    frames = []
    for t in thresholds:
        d = frames_data[t]
        frames.append(go.Frame(
            data=[go.Sunburst(
                ids=d["ids"],
                labels=d["labels"],
                parents=d["parents"],
                values=d["values"],
                hovertext=d["hovers"],
                hoverinfo="text",
                branchvalues="total",
                maxdepth=max_depth,
            )],
            name=str(t),
        ))
    fig.frames = frames

    steps = []
    for t in thresholds:
        step = {
            "args": [
                [str(t)],
                {"frame": {"duration": 300, "redraw": True}, "mode": "immediate"},
            ],
            "label": f"{t:.0f} PLN",
            "method": "animate",
        }
        steps.append(step)

    fig.update_layout(
        margin=dict(t=40, l=20, r=20, b=80),
        sliders=[{
            "active": 0,
            "currentvalue": {"prefix": "Hide transactions under: "},
            "steps": steps,
            "pad": {"t": 30},
        }],
    )

    return fig


def sunburst_data_to_json(df: pd.DataFrame) -> str:
    frames_data = build_sunburst_frames(df)
    return json.dumps({str(k): v for k, v in frames_data.items()})
