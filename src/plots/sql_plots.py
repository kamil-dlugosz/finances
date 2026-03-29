from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import yaml

from config import PROJECT_ROOT

logger = logging.getLogger(__name__)

QUERIES_PATH = PROJECT_ROOT / "config" / "dashboard_queries.yaml"


def _load_queries() -> list[dict]:
    if not QUERIES_PATH.exists():
        return []
    with open(QUERIES_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("dashboard_queries", [])


def _run_query_with_granularity(
    sql: str,
    granularity: str,
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    final_sql = sql.replace("{granularity}", granularity)
    try:
        return con.execute(final_sql).fetchdf()
    except duckdb.Error as exc:
        logger.warning("Query failed (granularity=%s): %s", granularity, exc)
        return pd.DataFrame()


def create_sql_plots(
    expense_df: pd.DataFrame,
    income_df: pd.DataFrame,
) -> list[go.Figure]:
    queries = _load_queries()
    if not queries:
        return []

    con = duckdb.connect(":memory:")
    con.register("transactions", expense_df)
    con.register("income", income_df)

    figures: list[go.Figure] = []
    granularities = ["year", "quarter", "month", "week"]

    for query_def in queries:
        name = query_def.get("name", "Unnamed")
        description = query_def.get("description", "")
        sql = query_def.get("sql", "")
        if not sql:
            continue

        fig = go.Figure()
        trace_count = 0

        for gran in granularities:
            result = _run_query_with_granularity(sql, gran, con)
            if result.empty:
                fig.add_trace(go.Bar(x=[], y=[], name=gran, visible=False))
                trace_count += 1
                continue

            x_col = result.columns[0]
            y_col = result.columns[1] if len(result.columns) > 1 else result.columns[0]

            fig.add_trace(go.Bar(
                x=result[x_col].astype(str),
                y=result[y_col],
                name=gran.capitalize(),
                visible=(gran == "month"),
            ))
            trace_count += 1

        buttons = []
        for i, gran in enumerate(granularities):
            visibility = [False] * trace_count
            visibility[i] = True
            buttons.append({
                "label": gran.capitalize(),
                "method": "update",
                "args": [{"visible": visibility}],
            })

        fig.update_layout(
            title=f"{name}: {description}",
            updatemenus=[{
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": 1.15,
                "buttons": buttons,
                "showactive": True,
            }],
            margin=dict(t=80, l=40, r=20, b=40),
        )
        figures.append(fig)

    con.close()
    return figures
