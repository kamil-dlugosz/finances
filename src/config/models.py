from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

TierNode = dict[str, "TierNode"] | list[str]


class TierTree:
    def __init__(self, tiers: TierNode) -> None:
        self._lookup: dict[str, tuple[str, ...]] = {}
        self._tier_depth: int = 0
        self.tree: TierNode = tiers
        self._build(tiers)

    def _build(self, tiers: TierNode) -> None:
        lookup: dict[str, tuple[str, ...]] = {}
        values_per_level: dict[int, set[str]] = defaultdict(set)
        leaf_depths: set[int] = set()

        def walk(node: TierNode, path: tuple[str, ...] = (), depth: int = 1) -> None:
            if isinstance(node, dict):
                for key, child in node.items():
                    if key in values_per_level[depth]:
                        raise ValueError(f"Duplicate value '{key}' at tier depth {depth}")
                    values_per_level[depth].add(key)
                    walk(child, path + (key,), depth + 1)
            elif isinstance(node, list):
                leaf_depths.add(depth)
                for leaf in node:
                    if leaf in values_per_level[depth]:
                        raise ValueError(f"Duplicate leaf '{leaf}' at tier depth {depth}")
                    values_per_level[depth].add(leaf)
                    lookup[leaf] = path + (leaf,)
            else:
                raise TypeError(f"Invalid node type {type(node)}; expected dict or list")

        walk(tiers)

        if len(leaf_depths) != 1:
            raise ValueError(f"Inconsistent leaf depths: {leaf_depths}")

        self._lookup = lookup
        self._tier_depth = leaf_depths.pop()

    @property
    def tier_depth(self) -> int:
        return self._tier_depth

    def path(self, leaf: str) -> tuple[str, ...]:
        try:
            return self._lookup[leaf]
        except KeyError:
            raise ValueError(f"Leaf '{leaf}' not found in tier tree") from None

    def contains(self, leaf: str) -> bool:
        return leaf in self._lookup


class PathsConfig(BaseModel):
    source_statements_raw_path: Path
    source_statements_path: Path

    @field_validator("*", mode="before")
    @classmethod
    def resolve_relative_to_project(cls, v: Any) -> Path:
        p = Path(v)
        if not p.is_absolute():
            return PROJECT_ROOT / p
        return p


class CsvLoadingConfig(BaseModel):
    date_type_columns: list[str]
    float_type_columns: list[str]
    column_name_mapping: dict[str, str]


class PreprocessingColumnsConfig(BaseModel):
    date_stamp_column: str
    amount_column: str
    expense_type_column: str


class HierarchyConfig(BaseModel):
    dimensions: list[str]
    tiers: dict

    @field_validator("tiers")
    @classmethod
    def validate_tier_structure(cls, v: dict) -> dict:
        TierTree(v)
        return v


class AppConfig(BaseModel):
    paths: PathsConfig
    csv_loading: CsvLoadingConfig
    preprocessing_columns: PreprocessingColumnsConfig
    hierarchy: HierarchyConfig
