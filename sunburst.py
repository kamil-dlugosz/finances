import pandas as pd
import plotly.graph_objects as go


def create_transaction_sunburst(df: pd.DataFrame):
    df = df.copy()

    nodes = []

    # ---- CategoryMonthYear
    month_sum = df.groupby("CategoryMonthYear")["Amount"].sum()
    for m, v in month_sum.items():
        nodes.append({
            "id": f"m_{m}",
            "parent": "",
            "label": m,
            "value": v
        })

    # ---- Category1
    lvl = df.groupby(["CategoryMonthYear","Category1"])["Amount"].sum().reset_index()
    for _, r in lvl.iterrows():
        nodes.append({
            "id": f"m_{r.CategoryMonthYear}|c1_{r.Category1}",
            "parent": f"m_{r.CategoryMonthYear}",
            "label": r.Category1,
            "value": r.Amount
        })

    # ---- Category2
    lvl = df.groupby(["CategoryMonthYear","Category1","Category2"])["Amount"].sum().reset_index()
    for _, r in lvl.iterrows():
        nodes.append({
            "id": f"m_{r.CategoryMonthYear}|c1_{r.Category1}|c2_{r.Category2}",
            "parent": f"m_{r.CategoryMonthYear}|c1_{r.Category1}",
            "label": r.Category2,
            "value": r.Amount
        })

    # ---- Category3
    lvl = df.groupby(["CategoryMonthYear","Category1","Category2","Category3"])["Amount"].sum().reset_index()
    for _, r in lvl.iterrows():
        nodes.append({
            "id": f"m_{r.CategoryMonthYear}|c1_{r.Category1}|c2_{r.Category2}|c3_{r.Category3}",
            "parent": f"m_{r.CategoryMonthYear}|c1_{r.Category1}|c2_{r.Category2}",
            "label": r.Category3,
            "value": r.Amount
        })

    # ---- Transactions (leaf nodes)
    for i, r in df.iterrows():
        nodes.append({
            "id": f"tx_{i}",
            "parent": f"m_{r.CategoryMonthYear}|c1_{r.Category1}|c2_{r.Category2}|c3_{r.Category3}",
            "label": r.Title,
            "value": r.Amount
        })

    nodes_df = pd.DataFrame(nodes)

    fig = go.Figure(go.Sunburst(
        ids=nodes_df["id"],
        labels=nodes_df["label"],
        parents=nodes_df["parent"],
        values=nodes_df["value"],
        branchvalues="total"
    ))

    fig.update_layout(margin=dict(t=20, l=20, r=20, b=20))

    return fig
