"""Interactive SQL viewer over preprocessed transaction data.

Run: python src/tools/sql_viewer.py

Commands:
  <SQL>          Execute a SQL query
  \\tables        List available tables and columns
  \\save <name>   Save the last query to config/dashboard_queries.yaml
  \\load <name>   Load a named query from config/dashboard_queries.yaml
  \\quit          Exit
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import sqlparse
import yaml
from rich.console import Console
from rich.table import Table

from config import PROJECT_ROOT
from etl.cache import EXPENSE_PARQUET, INCOME_PARQUET

QUERIES_PATH = PROJECT_ROOT / "config" / "dashboard_queries.yaml"

console = Console()


def _load_queries_config() -> dict:
    if not QUERIES_PATH.exists():
        return {"dashboard_queries": []}
    try:
        with open(QUERIES_PATH, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        console.print(f"[red]Failed to parse {QUERIES_PATH}: {exc}[/red]")
        return {"dashboard_queries": []}
    if not isinstance(raw, dict):
        console.print(f"[red]Expected mapping in {QUERIES_PATH}, got {type(raw).__name__}[/red]")
        return {"dashboard_queries": []}
    return raw


def _save_queries_config(data: dict) -> None:
    with open(QUERIES_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _format_sql(sql: str) -> str:
    return sqlparse.format(
        sql,
        reindent=True,
        keyword_case="upper",
        indent_width=2,
    ).strip()


def _display_result(result: duckdb.DuckDBPyRelation) -> None:
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()

    table = Table(show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)

    for row in rows[:200]:
        table.add_row(*(str(v) for v in row))

    console.print(table)
    if len(rows) > 200:
        console.print(f"[dim]... showing 200 of {len(rows)} rows[/dim]")
    else:
        console.print(f"[dim]{len(rows)} row(s)[/dim]")


def _cmd_tables(con: duckdb.DuckDBPyConnection) -> None:
    for table_name in ["transactions", "income"]:
        try:
            result = con.execute(f"DESCRIBE {table_name}")
            cols = result.fetchall()
            console.print(f"\n[bold]{table_name}[/bold]")
            t = Table(show_header=True, header_style="bold green")
            t.add_column("Column")
            t.add_column("Type")
            for col_info in cols:
                t.add_row(str(col_info[0]), str(col_info[1]))
            console.print(t)
        except Exception as e:
            console.print(f"[red]Could not describe {table_name}: {e}[/red]")


def _cmd_save(name: str, last_sql: str) -> None:
    if not last_sql:
        console.print("[yellow]No query to save.[/yellow]")
        return

    formatted = _format_sql(last_sql)
    data = _load_queries_config()
    queries = data.get("dashboard_queries", [])
    if not isinstance(queries, list):
        console.print("[yellow]dashboard_queries is not a list — starting fresh[/yellow]")
        queries = []

    for q in queries:
        if not isinstance(q, dict):
            continue
        if q.get("name") == name:
            q["sql"] = formatted
            console.print(f"[green]Updated existing query '{name}'[/green]")
            _save_queries_config(data)
            return

    queries.append({
        "name": name,
        "description": "",
        "sql": formatted,
    })
    data["dashboard_queries"] = queries
    _save_queries_config(data)
    console.print(f"[green]Saved query as '{name}' → {QUERIES_PATH}[/green]")
    console.print(f"[dim]{formatted}[/dim]")


def _cmd_load(name: str) -> str | None:
    data = _load_queries_config()
    queries = data.get("dashboard_queries", [])
    if not isinstance(queries, list):
        queries = []
    for q in queries:
        if isinstance(q, dict) and q.get("name") == name:
            sql = q.get("sql", "")
            console.print(f"[green]Loaded '{name}':[/green]")
            console.print(f"[dim]{sql}[/dim]")
            return sql
    console.print(f"[yellow]Query '{name}' not found.[/yellow]")
    available = [q.get("name") for q in queries if isinstance(q, dict)]
    if available:
        console.print(f"[dim]Available: {', '.join(available)}[/dim]")
    return None


def main() -> None:
    if not EXPENSE_PARQUET.exists():
        console.print("[red]No cached data. Run 'python main.py' first.[/red]")
        sys.exit(1)

    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE transactions AS SELECT * FROM read_parquet(?)", [str(EXPENSE_PARQUET)])
    if INCOME_PARQUET.exists():
        con.execute("CREATE TABLE income AS SELECT * FROM read_parquet(?)", [str(INCOME_PARQUET)])

    console.print("[bold]SQL Viewer[/bold] — type SQL or use \\tables, \\save <name>, \\load <name>, \\quit")
    console.print()

    last_sql = ""

    while True:
        try:
            line = console.input("[bold blue]sql>[/bold blue] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue

        if line.lower() in ("\\quit", "\\q", "exit", "quit"):
            break

        if line.lower() == "\\tables":
            _cmd_tables(con)
            continue

        if line.lower().startswith("\\save "):
            name = line[6:].strip()
            if not name:
                console.print("[yellow]Usage: \\save <name>[/yellow]")
                continue
            _cmd_save(name, last_sql)
            continue

        if line.lower().startswith("\\load "):
            name = line[6:].strip()
            loaded = _cmd_load(name)
            if loaded:
                last_sql = loaded
            continue

        try:
            result = con.execute(line)
            _display_result(result)
            last_sql = line
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    con.close()
    console.print("[dim]Goodbye.[/dim]")


if __name__ == "__main__":
    main()
