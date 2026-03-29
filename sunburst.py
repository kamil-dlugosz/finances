import pandas as pd
import plotly.graph_objects as go


def _create_nodes(df):
    category_columns_names = [c for c in df.columns if c.startswith("Category")]

    leaf_agg = df.groupby(category_columns_names)["Amount"].sum()

    levels = {}
    for depth in range(1, len(category_columns_names) + 1):
        levels[depth] = leaf_agg.groupby(level=list(range(depth))).sum()

    ids, parents, labels, values = [], [], [], []

    # Category and month nodes
    for depth, ser in levels.items():
        for month, amount in ser.items():
            parent = f"m_{month}"

            if depth == 1:  # month node
                node_id = parent
                node_parent = ""
                label = month
            else:
                continue
                # if depth > 2:
                #     parent += "|" + "|".join(f"c{i}_{v}" for i, v in enumerate(idx[1:depth-1], start=1))
                # node_id = parent + f"|c{depth-1}_{idx[depth-1]}"
                # node_parent = parent
                # label = idx[depth-1]

            ids.append(node_id)
            parents.append(node_parent)
            values.append(amount)
            labels.append(label)

    # Transaction leaves
    # for row in df.itertuples(index=True):
    #     parent = f"m_{row.CategoryMonthYear}"
    #     for i, col in enumerate(cat_cols, start=1):
    #         parent += f"|c{i}_{getattr(row, col)}"
    #
    #     ids.append(parent + f"|tx_{row.Index}")
    #     parents.append(parent)
    #     values.append(row.Amount)
    #     # Optionally show last category + amount for leaf label
    #     labels.append(f"{getattr(row, cat_cols[-1])}: {row.Amount}")

    return ids, parents, labels, values


def create_transaction_sunburst(df: pd.DataFrame):
    ids, parents, labels, values = _create_nodes(df)

    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total"
    ))

    fig.update_layout(margin=dict(t=20, l=20, r=20, b=20))

    return fig


def create_transaction_sunburst_old(df: pd.DataFrame):
    df = df.copy()

    nodes = _create_nodes_old(df)

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


def _create_nodes_old(df):
    nodes = []
    # ---- CategoryMonthYear
    month_sum = df.groupby("CategoryMonthYear")["Amount"].sum()
    for m, v in month_sum.items():
        nodes.append(
            {
                "id": f"m_{m}",
                "parent": "",
                "label": m,
                "value": v
            }
        )
    # ---- Category1
    lvl = df.groupby(
        ["CategoryMonthYear", "Category1"]
    )["Amount"].sum().reset_index()
    for _, r in lvl.iterrows():
        nodes.append(
            {
                "id": f"m_{r.CategoryMonthYear}|"
                      f"c1_{r['Category1']}",
                "parent": f"m_{r.CategoryMonthYear}",
                "label": r['Category1'],
                "value": r['Amount']
            }
        )
    # ---- Category2
    lvl = df.groupby(
        ["CategoryMonthYear", "Category1", "Category2"]
    )["Amount"].sum().reset_index()
    for _, r in lvl.iterrows():
        nodes.append(
            {
                "id": f"m_{r.CategoryMonthYear}|"
                      f"c1_{r['Category1']}|"
                      f"c2_{r['Category2']}",
                "parent": f"m_{r.CategoryMonthYear}|"
                          f"c1_{r['Category1']}",
                "label": r['Category2'],
                "value": r['Amount']
            }
        )
    # ---- Category3
    lvl = df.groupby(
        ["CategoryMonthYear", "Category1", "Category2", "Category3"]
        )["Amount"].sum().reset_index()
    for _, r in lvl.iterrows():
        nodes.append(
            {
                "id": f"m_{r.CategoryMonthYear}|"
                      f"c1_{r['Category1']}|"
                      f"c2_{r['Category2']}|"
                      f"c3_{r['Category3']}",
                "parent": f"m_{r.CategoryMonthYear}|"
                          f"c1_{r['Category1']}|"
                          f"c2_{r['Category2']}",
                "label": r['Category3'],
                "value": r['Amount']
            }
        )
    # ---- Transactions (leaf nodes)
    for i, r in df.iterrows():
        nodes.append(
            {
                "id": f"tx_{i}",
                "parent": f"m_{r.CategoryMonthYear}|"
                          f"c1_{r.Category1}|"
                          f"c2_{r.Category2}|"
                          f"c3_{r.Category3}",
                "label": r.Title,
                "value": r.Amount
            }
        )
    return nodes
