from __future__ import annotations
from dataclasses import dataclass, field

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import get_config, get_tier_tree


@dataclass
class SuspectEntry:
    expense_type: str
    parent_tier: str
    avg_similarity: float
    sample_titles: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    suspects: list[SuspectEntry] = field(default_factory=list)

    def summary(self) -> str:
        if not self.suspects:
            return "All ExpenseType values look consistent within their parent tier groups."
        lines = [f"Found {len(self.suspects)} suspect ExpenseType(s):\n"]
        for s in self.suspects:
            lines.append(
                f"  - '{s.expense_type}' in '{s.parent_tier}' "
                f"(avg cosine sim={s.avg_similarity:.3f}, "
                f"samples: {s.sample_titles[:3]})"
            )
        return "\n".join(lines)


def validate_expense_types(
    df: pd.DataFrame,
    similarity_threshold: float = 0.05,
) -> ValidationReport:
    """Flag expense types whose TF-IDF title similarity to siblings is below
    ``similarity_threshold`` (range 0..1; lower means more dissimilar).
    Default 0.05 is intentionally aggressive — raise to ~0.15 for fewer false positives."""
    expense_col = get_config().preprocessing_columns.expense_type_column
    depth = get_tier_tree().tier_depth
    parent_tier_col = f"Tier{max(1, depth - 1)}"
    report = ValidationReport()

    for parent_tier, group in df.groupby(parent_tier_col):
        expense_types = group[expense_col].unique()
        if len(expense_types) < 2:
            continue

        type_texts: dict[str, str] = {}
        for et in expense_types:
            et_rows = group[group[expense_col] == et]
            combined = " ".join(et_rows.get("Title", pd.Series(dtype=str)).fillna("").tolist())
            type_texts[et] = combined

        texts = list(type_texts.values())
        keys = list(type_texts.keys())

        if not any(t.strip() for t in texts):
            continue

        vectorizer = TfidfVectorizer(max_features=200)
        try:
            X = vectorizer.fit_transform(texts)
        except ValueError:
            continue

        sim_matrix = cosine_similarity(X)

        for i, et in enumerate(keys):
            others = [sim_matrix[i][j] for j in range(len(keys)) if j != i]
            avg_sim = sum(others) / len(others) if others else 1.0

            if avg_sim < similarity_threshold:
                et_rows = group[group[expense_col] == et]
                samples = et_rows.get("Title", pd.Series(dtype=str)).head(3).tolist()
                report.suspects.append(SuspectEntry(
                    expense_type=et,
                    parent_tier=str(parent_tier),
                    avg_similarity=round(avg_sim, 4),
                    sample_titles=samples,
                ))

    return report
