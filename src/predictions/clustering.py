from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from predictions.cache import load_prediction_cache, save_prediction_cache

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    tier_path: str
    n_clusters: int
    seed: int
    clusters: list[dict] = field(default_factory=list)


def cluster_tier(
    df: pd.DataFrame,
    tier_path: str,
    n_clusters: int = 5,
    seed: int = 42,
) -> ClusterResult:
    cache_key = f"cluster_{tier_path.replace('/', '_')}_{n_clusters}_{seed}"
    cached = load_prediction_cache(cache_key)
    if cached:
        data = json.loads(cached)
        return ClusterResult(**data)

    segments = tier_path.split("/")

    def _matches(full_path: str) -> bool:
        if pd.isna(full_path):
            return False
        parts = full_path.split("|")
        for i in range(len(parts) - len(segments) + 1):
            if parts[i : i + len(segments)] == segments:
                return True
        return False

    mask = df["FullPath"].map(_matches)
    subset = df[mask].copy()

    if subset.empty:
        logger.warning("No rows match tier path '%s'", tier_path)
        return ClusterResult(tier_path=tier_path, n_clusters=0, seed=seed, clusters=[])

    if len(subset) < n_clusters:
        logger.warning("Only %d rows for path '%s' — fewer than %d clusters", len(subset), tier_path, n_clusters)
        n_clusters = max(1, len(subset))

    text_col = subset.apply(
        lambda r: f"{r.get('Title', '')} {r.get('Counterparty', '')}",
        axis=1,
    )

    vectorizer = TfidfVectorizer(max_features=500, stop_words=None)
    try:
        X = vectorizer.fit_transform(text_col)
    except ValueError:
        logger.warning("Empty vocabulary for tier path '%s'", tier_path)
        return ClusterResult(tier_path=tier_path, n_clusters=0, seed=seed, clusters=[])

    km = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    labels = km.fit_predict(X)

    feature_names = vectorizer.get_feature_names_out()
    clusters: list[dict] = []
    for cid in range(n_clusters):
        cluster_mask = labels == cid
        cluster_size = int(cluster_mask.sum())
        center = km.cluster_centers_[cid]
        top_indices = center.argsort()[-5:][::-1]
        top_words = [feature_names[i] for i in top_indices]
        clusters.append({
            "cluster_id": cid,
            "size": cluster_size,
            "keywords": top_words,
        })

    result = ClusterResult(
        tier_path=tier_path,
        n_clusters=n_clusters,
        seed=seed,
        clusters=clusters,
    )
    save_prediction_cache(cache_key, json.dumps(result.__dict__))
    return result
