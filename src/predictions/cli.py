"""Predictions CLI — run with: python -m predictions <command>"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PROJECT_ROOT
from etl.cache import load_cache, EXPENSE_PARQUET
from predictions.clustering import cluster_tier
from predictions.validator import validate_expense_types
from predictions.proposals import list_proposals

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CUSTOM_TIERS_PATH = PROJECT_ROOT / "config" / "custom_tiers.yaml"


def _load_expense_df() -> pd.DataFrame:
    if not EXPENSE_PARQUET.exists():
        logger.error("No cached data. Run 'python main.py' first.")
        sys.exit(1)
    return pd.read_parquet(EXPENSE_PARQUET)


def cmd_cluster(args: argparse.Namespace) -> None:
    df = _load_expense_df()
    result = cluster_tier(df, args.tier, args.n, args.seed)
    print(f"\nClustering: {result.tier_path} → {result.n_clusters} clusters (seed={result.seed})\n")
    for c in result.clusters:
        print(f"  Cluster {c['cluster_id']}: {c['size']} transactions")
        print(f"    Keywords: {', '.join(c['keywords'])}")
    print()


def cmd_validate(args: argparse.Namespace) -> None:
    df = _load_expense_df()
    report = validate_expense_types(df)
    print(report.summary())


def cmd_propose(args: argparse.Namespace) -> None:
    proposals = list_proposals()
    print("\nAvailable prediction/analysis proposals:\n")
    for i, p in enumerate(proposals, 1):
        print(f"  {i}. {p['name']}")
        print(f"     {p['description']}\n")


def cmd_add_cluster(args: argparse.Namespace) -> None:
    if args.cluster_id < 0:
        logger.error("--cluster-id must be >= 0, got %d", args.cluster_id)
        sys.exit(1)

    df = _load_expense_df()
    result = cluster_tier(df, args.tier, max(args.cluster_id + 1, 2), args.seed)

    if args.cluster_id >= len(result.clusters):
        logger.error("Cluster ID %d not found (max: %d)", args.cluster_id, len(result.clusters) - 1)
        sys.exit(1)

    cluster = result.clusters[args.cluster_id]
    tier_parts = args.tier.split("/")

    new_rule = {
        "match": {
            "tier_path": args.tier,
            "keywords": cluster["keywords"],
        },
        "assign": {},
    }
    for i, part in enumerate(tier_parts, 1):
        new_rule["assign"][f"tier_{i}"] = part
    new_rule["assign"][f"tier_{len(tier_parts) + 1}"] = args.name

    if CUSTOM_TIERS_PATH.exists():
        with open(CUSTOM_TIERS_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    rules = data.get("custom_tiers", [])
    rules.append(new_rule)
    data["custom_tiers"] = rules

    with open(CUSTOM_TIERS_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    logger.info("Added custom tier '%s' to %s", args.name, CUSTOM_TIERS_PATH)
    print(f"\nRule added for cluster {args.cluster_id} → '{args.name}'")
    print(f"Keywords: {cluster['keywords']}")
    print(f"File: {CUSTOM_TIERS_PATH}\n")


def main() -> None:
    parser = argparse.ArgumentParser(prog="predictions", description="Transaction prediction tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_cluster = sub.add_parser("cluster", help="Cluster transactions in a tier")
    p_cluster.add_argument("--tier", required=True, help='Tier path, e.g. "Utrzymanie/Wydatki bieżące"')
    p_cluster.add_argument("--n", type=int, default=5, help="Number of clusters")
    p_cluster.add_argument("--seed", type=int, default=42, help="Random seed")
    p_cluster.set_defaults(func=cmd_cluster)

    p_validate = sub.add_parser("validate", help="Validate ExpenseType labels")
    p_validate.set_defaults(func=cmd_validate)

    p_propose = sub.add_parser("propose", help="List analysis proposals")
    p_propose.set_defaults(func=cmd_propose)

    p_add = sub.add_parser("add-cluster", help="Add a cluster as a custom tier rule")
    p_add.add_argument("--tier", required=True, help='Tier path, e.g. "Utrzymanie/Wydatki bieżące"')
    p_add.add_argument("--cluster-id", type=int, required=True, help="Cluster ID to add (>= 0)")
    p_add.add_argument("--name", required=True, help="Name for the new sub-tier")
    p_add.add_argument("--seed", type=int, default=42, help="Random seed")
    p_add.set_defaults(func=cmd_add_cluster)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
