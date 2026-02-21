"""
Epic 4 — Risk Scoring Engine

Computes a composite risk score from rule violations and classifies
the transaction into safe / monitor / critical buckets.
"""
from typing import List
from backend.core.validation_models import RuleViolation


# Weight matrix (spec §3.2)
SEVERITY_WEIGHTS = {
    "critical": 30,
    "high":     20,
    "medium":   10,
    "low":       5,
}


def calculate_score(violations: List[RuleViolation]) -> int:
    """Sum violation weights, capped at 100."""
    raw = sum(v.weight for v in violations)
    return min(100, raw)


def classify_risk(score: int) -> str:
    """Map a numeric score to a classification label."""
    if score <= 30:
        return "safe"
    if score <= 70:
        return "monitor"
    return "critical"
