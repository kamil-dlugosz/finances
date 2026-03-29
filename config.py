from __future__ import annotations

import yaml

from collections import defaultdict

from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Tuple


TierNode = dict[str, 'TierNode'] | list[str]


class TierTree:
    def __init__(self, tiers: TierNode) -> None:
        self._lookup: Dict[str, Tuple[str, ...]] = {}
        self._build(tiers)
        self.tree = tiers

    def _build(self, tiers: dict):
        lookup: Dict[str, Tuple[str, ...]] = {}
        values_per_level = defaultdict(set)
        leaf_depths = set()

        def walk(node, path=(), depth=1):
            if isinstance(node, dict):
                for key, child in node.items():
                    if key in values_per_level[depth]:
                        raise ValueError(f"Duplicate value '{key}' at level {depth}")
                    values_per_level[depth].add(key)
                    walk(child, path + (key,), depth + 1)
            elif isinstance(node, list):
                leaf_depths.add(depth)
                for leaf in node:
                    if leaf in values_per_level[depth]:
                        raise ValueError(f"Duplicate leaf '{leaf}' at level {depth}")
                    values_per_level[depth].add(leaf)
                    lookup[leaf] = path + (leaf,)
            else:
                raise TypeError(f"Invalid node type {type(node)}; expected dict or list")

        walk(tiers)

        if len(leaf_depths) != 1:
            raise ValueError(f"Inconsistent leaf depths: {leaf_depths}")

        self._lookup = lookup

    def path(self, leaf: str) -> Tuple[str, ...]:
        return self._lookup[leaf]


with open("config.yaml", "r", encoding="utf-8") as f:
    _config = yaml.safe_load(f)

PATHS = SimpleNamespace(
    SOURCE_STATEMENTS=Path(_config["paths"]["source_statements_path"]),
    PREPROCESSED_STATEMENTS=Path(_config["paths"]["preprocessed_statements_path"]),
)

CSV_LOADING = SimpleNamespace(
    DATE_TYPE_COLUMNS=_config["csv_loading"]["date_type_columns"],
    FLOAT_TYPE_COLUMNS=_config["csv_loading"]["float_type_columns"],
    COLUMN_NAME_MAPPING=_config["csv_loading"]["column_name_mapping"],
)

PREPROCESSING_COLUMNS = SimpleNamespace(
    DATE_STAMP_COLUMN=_config["preprocessing_columns"]["date_stamp_column"],
    AMOUNT_COLUMN=_config["preprocessing_columns"]["amount_column"],
    EXPENSE_TYPE_COLUMN=_config["preprocessing_columns"]["expense_type_column"],
)

HIERARCHY = SimpleNamespace(
    DIMENTIONS=_config["hierarchy"]["dimensions"],
    TIERS=TierTree(_config["hierarchy"]["tiers"]),
)
