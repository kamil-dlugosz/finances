from pathlib import Path

import yaml

with open("config.yaml", "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f)

SOURCE_STATEMENTS_PATH = Path(_config["paths"]["source_statements_path"])
PREPROCESSED_STATEMENTS_PATH = Path(_config["paths"]["preprocessed_statements_path"])

DATE_TYPE_COLUMNS = _config["csv_loading"]["date_type_columns"]
FLOAT_TYPE_COLUMNS = _config["csv_loading"]["float_type_columns"]
COLUMN_NAME_MAPPING = _config["csv_loading"]["column_name_mapping"]

DATE_STAMP_COLUMN = _config["date_stamp_column"]
EXPENSE_TYPE_COLUMN = _config["expense_type_column"]

CATEGORY_STRUCTURE = _config["labeling"]["category_structure"]
