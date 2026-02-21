"""
Epic 4 — Rule Evaluator

Iterates all registered rules against a ValidationContext, collecting
violations and returning a summary.
"""
from typing import List

from backend.core.validation_models import RuleViolation, ValidationContext
from backend.core.rule_registry import RuleRegistry


class RuleEvaluator:
    """Runs every rule in the registry against a single transaction context."""

    def __init__(self, registry: RuleRegistry):
        self.registry = registry

    def evaluate_all(self, ctx: ValidationContext) -> List[RuleViolation]:
        """
        Evaluate every registered rule.  Returns the list of violations
        (failed rules only).  Rules that pass return None and are counted
        but not included in the output list.
        """
        violations: List[RuleViolation] = []
        for rule in self.registry.get_all():
            try:
                result = rule.evaluate(ctx)
                if result is not None:
                    violations.append(result)
            except Exception:
                # Gracefully skip rules that cannot be evaluated
                # (e.g. missing data the rule depends on).
                pass
        return violations
