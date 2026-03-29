# Finances Dashboard

Interactive single-file HTML dashboard for analysing personal bank transactions.
Includes a sunburst chart with drill-down to individual transactions, hierarchical
bar plots by time period, income bar chart, income-vs-expenses waterfall, and
SQL-driven custom query plots.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (or Poetry)

## Installation

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install pandas plotly pydantic pyyaml pyarrow duckdb scikit-learn sqlparse rich numpy pytest
```

## Project Structure

```
finances/
├── main.py                   # entry point
├── pyproject.toml
├── README.md
├── config/                   # YAML configuration files
│   ├── hierarchy.yaml        # dimensions and expense category tiers
│   ├── pipeline.yaml         # paths, CSV column mappings, preprocessing
│   ├── dashboard_queries.yaml # SQL queries for dashboard plots
│   └── custom_tiers.yaml    # keyword rules for tier reclassification
├── src/                      # all application code
│   ├── config/               # Pydantic models, tier tree, config loader
│   ├── etl/                  # CSV loading, preprocessing, cache
│   ├── plots/                # sunburst, barplots, income, sql_plots
│   ├── predictions/          # clustering, validation, CLI
│   ├── web/                  # HTML renderer, template, legend.js
│   └── tools/                # anonymizer, sql_viewer
├── tests/                    # pytest unit tests
├── resources/                # input data (gitignored)
│   └── statements/           # bank/ and anonymized/ CSVs
├── dist/                     # generated output.html (gitignored)
└── .cache/                   # precomputed parquets, fingerprint (gitignored)
```

## Configuration

All YAML configuration lives in `config/` at the project root:

| File | Purpose |
|---|---|
| `config/hierarchy.yaml` | Time dimensions (Year, Month) and nested expense category tree |
| `config/pipeline.yaml` | Source paths, CSV column types and name mappings, preprocessing column roles |
| `config/dashboard_queries.yaml` | SQL queries that drive the custom query plots section |
| `config/custom_tiers.yaml` | Keyword-matching rules that reclassify transactions into custom tiers |

### hierarchy.yaml

- **dimensions** — time dimensions used as outer sunburst rings (Year, Month, etc.)
- **tiers** — nested expense category tree (depth must be uniform across all branches)

### pipeline.yaml

- **paths** — where to find raw and anonymized statements
- **csv_loading** — date columns, float columns, Polish-to-English column name mapping
- **preprocessing_columns** — which mapped columns serve as date stamp, amount, expense type

## Running the dashboard

```bash
python main.py
```

This generates `dist/output.html` — open it in a browser.

To force recomputation (ignore cache):

```bash
python main.py --force
```

The cache (`.cache/`) stores preprocessed parquets and a source fingerprint.
If any source CSV changes (added/removed file, row count change, file size change),
the cache auto-invalidates on the next run.

## Anonymizing statements

Place raw bank CSV exports in `resources/statements/bank/`, then:

```bash
python src/tools/anonymizer.py
```

Anonymized files appear in `resources/statements/anonymized/`.

## SQL Viewer

Interactive REPL for querying preprocessed data with SQL (powered by DuckDB):

```bash
python src/tools/sql_viewer.py
```

Available tables: `transactions`, `income`.

| Command | Description |
|---|---|
| `<SQL>` | Execute a SQL query, display results as a table |
| `\tables` | List tables and their columns |
| `\save <name>` | Format and save the last query to `config/dashboard_queries.yaml` |
| `\load <name>` | Load a named query from `config/dashboard_queries.yaml` |
| `\quit` | Exit |

## Predictions CLI

Transaction analysis and clustering tools:

```bash
# Cluster transactions within a tier
PYTHONPATH=src python -m predictions cluster --tier "Utrzymanie/Wydatki bieżące" --n 5

# Validate ExpenseType label consistency
PYTHONPATH=src python -m predictions validate

# List available analysis proposals
PYTHONPATH=src python -m predictions propose

# Add a discovered cluster as a custom tier rule
PYTHONPATH=src python -m predictions add-cluster --tier "Utrzymanie/Wydatki bieżące" --cluster-id 2 --name "Chemia domowa"
```

The `add-cluster` command appends a keyword-matching rule to `config/custom_tiers.yaml`.
On the next `python main.py` run, matching transactions get reclassified.

## Running tests

```bash
python -m pytest tests/
```

Tests mirror the module structure:

```
tests/
├── conftest.py          # shared fixtures
├── config/              # models, tier tree, loader
├── etl/                 # loading, preprocessing, cache
├── plots/               # sunburst, barplots, income, sql_plots
├── predictions/         # clustering, validator, proposals
└── tools/               # anonymizer, sql_viewer
```
