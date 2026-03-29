from __future__ import annotations

PROPOSALS: list[dict[str, str]] = [
    {
        "name": "Anomaly Detection",
        "description": "Flag transactions with unusually high amounts for their tier category using z-score or IQR.",
    },
    {
        "name": "Seasonal Trend Detection",
        "description": "Identify tiers with strong seasonal spending patterns (e.g., higher heating in winter).",
    },
    {
        "name": "Counterparty Frequency",
        "description": "Rank counterparties by transaction count and total spend to find top merchants.",
    },
    {
        "name": "Recurring Transactions",
        "description": "Detect likely subscriptions by finding regular-interval, fixed-amount transactions.",
    },
    {
        "name": "Spending Velocity",
        "description": "Track week-over-week or month-over-month spending growth rate per tier.",
    },
    {
        "name": "Cross-Tier Correlation",
        "description": "Identify tiers whose spending moves together (e.g., dining out + entertainment).",
    },
]


def list_proposals() -> list[dict[str, str]]:
    return list(PROPOSALS)
