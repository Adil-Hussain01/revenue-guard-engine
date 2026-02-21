"""
Epic 4 — Reconciliation Engine

Central orchestrator that:
  1. Fetches order data from the CRM Store
  2. Looks up matching invoices / payments from the Finance Store
  3. Builds a ValidationContext
  4. Runs the RuleEvaluator
  5. Computes risk score via the RiskScoringEngine
  6. Logs every step to the AuditLogger
  7. Stores and returns the ValidationResult
"""
import uuid
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from backend.api.crm_store import CRMStore
from backend.api.finance_store import FinanceStore
from backend.core.audit_logger import AuditLogger
from backend.core.audit_models import RuleResult as AuditRuleResult
from backend.core.rule_evaluator import RuleEvaluator
from backend.core.rule_registry import RuleRegistry, build_default_registry, CSI001_GhostInvoice
from backend.core import risk_scoring_engine
from backend.core.validation_models import (
    RuleViolation,
    ValidationContext,
    ValidationResult,
    ValidationStatistics,
    RiskDistribution,
    RiskDistributionBucket,
)


class ReconciliationEngine:
    """Orchestrates CRM ↔ Finance reconciliation."""

    def __init__(
        self,
        crm_store: CRMStore,
        finance_store: FinanceStore,
        audit_logger: Optional[AuditLogger] = None,
        registry: Optional[RuleRegistry] = None,
    ):
        self.crm = crm_store
        self.fin = finance_store
        self.audit = audit_logger
        self.registry = registry or build_default_registry()
        self.evaluator = RuleEvaluator(self.registry)

        # In-memory results cache (order_id → ValidationResult)
        self._results: Dict[str, ValidationResult] = {}

    # ------------------------------------------------------------------
    # Core: single transaction
    # ------------------------------------------------------------------

    def reconcile_transaction(self, order_id: str) -> ValidationResult:
        correlation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # 1. Fetch order from CRM
        order = self.crm.get_order(order_id)
        if not order:
            result = ValidationResult(
                order_id=order_id,
                risk_score=100,
                risk_classification="critical",
                rules_evaluated=0,
                rules_failed=1,
                violations=[
                    RuleViolation(
                        rule_id="SYS-001",
                        rule_name="Order Not Found",
                        severity="critical",
                        weight=100,
                        message=f"Order {order_id} does not exist in the CRM system",
                    )
                ],
                validated_at=now,
            )
            self._results[order_id] = result
            return result

        # 2. Lookup invoices from Finance (match by order_id)
        matching_invoices = [inv for inv in self.fin.list_invoices() if inv.order_id == order_id]
        primary_invoice = matching_invoices[0] if matching_invoices else None

        # 3. Gather payments for the primary invoice
        payments = []
        if primary_invoice:
            payments = [p for p in self.fin.list_payments() if p.invoice_id == primary_invoice.invoice_id]

        # 4. Gather ledger entries for the primary invoice
        ledger_entries = []
        if primary_invoice:
            ledger_entries = [e for e in self.fin.list_ledger() if e.invoice_id == primary_invoice.invoice_id]

        # 5. Build context
        ctx = ValidationContext(
            order=order,
            invoice=primary_invoice,
            invoices=matching_invoices,
            payments=payments,
            ledger_entries=ledger_entries,
        )

        # 6. Audit: validation start
        if self.audit:
            try:
                self.audit.log_validation_start(order_id, correlation_id)
            except Exception:
                pass

        # 7. Evaluate rules
        violations = self.evaluator.evaluate_all(ctx)
        total_rules = len(self.registry.get_all())

        # 8. Audit: individual rule results
        if self.audit:
            for rule in self.registry.get_all():
                violation = next((v for v in violations if v.rule_id == rule.rule_id), None)
                try:
                    self.audit.log_rule_result(
                        transaction_id=order_id,
                        rule_id=rule.rule_id,
                        result=AuditRuleResult(
                            rule_name=rule.rule_name,
                            passed=violation is None,
                            details={"message": violation.message} if violation else {},
                        ),
                        correlation_id=correlation_id,
                    )
                except Exception:
                    pass

        # 9. Compute risk score
        score = risk_scoring_engine.calculate_score(violations)
        classification = risk_scoring_engine.classify_risk(score)

        # 10. Audit: risk score
        if self.audit:
            try:
                self.audit.log_risk_score(order_id, score, classification, correlation_id)
            except Exception:
                pass

        # 11. Build result
        result = ValidationResult(
            order_id=order_id,
            risk_score=score,
            risk_classification=classification,
            rules_evaluated=total_rules,
            rules_passed=total_rules - len(violations),
            rules_failed=len([v for v in violations if v.severity in ("critical", "high")]),
            rules_warned=len([v for v in violations if v.severity in ("medium", "low")]),
            violations=violations,
            validated_at=now,
        )
        self._results[order_id] = result

        # 12. Audit: completion
        if self.audit:
            from backend.core.audit_models import ValidationResult as AuditValidationResult
            try:
                self.audit.log_validation_complete(
                    transaction_id=order_id,
                    result=AuditValidationResult(
                        risk_score=score,
                        risk_classification=classification,
                        decision="pass" if classification == "safe" else "review",
                    ),
                    correlation_id=correlation_id,
                )
            except Exception:
                pass

        return result

    # ------------------------------------------------------------------
    # Batch & full-scan
    # ------------------------------------------------------------------

    def reconcile_all(self) -> List[ValidationResult]:
        """Run validation across every order in the CRM store."""
        results = []
        all_orders, _ = self.crm.get_orders(page=1, page_size=100_000)
        for order in all_orders:
            result = self.reconcile_transaction(order.order_id)
            results.append(result)

        # Also run ghost-invoice detection (CSI-001 externally)
        self._detect_ghost_invoices()
        return results

    def _detect_ghost_invoices(self):
        """Scan Finance invoices for references to non-existent CRM orders."""
        crm_order_ids = set(self.crm.orders.keys())
        for inv in self.fin.list_invoices():
            if inv.order_id not in crm_order_ids:
                # Attach the ghost invoice as a violation on a synthetic result
                ghost_result = ValidationResult(
                    order_id=inv.order_id,
                    risk_score=30,
                    risk_classification="monitor",
                    rules_evaluated=1,
                    rules_failed=1,
                    violations=[
                        RuleViolation(
                            rule_id="CSI-001",
                            rule_name="Ghost Invoice",
                            severity="critical",
                            weight=30,
                            message=f"Invoice {inv.invoice_id} references order {inv.order_id} that does not exist in CRM",
                            expected_value="order exists",
                            actual_value="not found",
                        )
                    ],
                    validated_at=datetime.now(timezone.utc),
                )
                self._results[inv.order_id] = ghost_result

    def reconcile_batch(self, order_ids: List[str]) -> List[ValidationResult]:
        """Validate a specific list of order IDs."""
        return [self.reconcile_transaction(oid) for oid in order_ids]

    # ------------------------------------------------------------------
    # Results access
    # ------------------------------------------------------------------

    def get_result(self, order_id: str) -> Optional[ValidationResult]:
        return self._results.get(order_id)

    def get_all_results(self) -> List[ValidationResult]:
        return list(self._results.values())

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> ValidationStatistics:
        results = self.get_all_results()
        if not results:
            return ValidationStatistics(
                total_transactions=len(self.crm.orders),
                total_validated=0,
                safe_count=0,
                monitor_count=0,
                critical_count=0,
                average_risk_score=0.0,
            )

        safe = sum(1 for r in results if r.risk_classification == "safe")
        monitor = sum(1 for r in results if r.risk_classification == "monitor")
        critical = sum(1 for r in results if r.risk_classification == "critical")
        avg_score = sum(r.risk_score for r in results) / len(results)

        # Top violated rules
        rule_counter: Counter = Counter()
        for r in results:
            for v in r.violations:
                rule_counter[v.rule_id] += 1
        top_rules = [
            {"rule_id": rid, "count": cnt}
            for rid, cnt in rule_counter.most_common(5)
        ]

        return ValidationStatistics(
            total_transactions=len(self.crm.orders),
            total_validated=len(results),
            safe_count=safe,
            monitor_count=monitor,
            critical_count=critical,
            average_risk_score=round(avg_score, 2),
            top_violated_rules=top_rules,
        )

    def get_risk_distribution(self) -> RiskDistribution:
        results = self.get_all_results()
        buckets_map = {f"{i*10}-{i*10+9}": 0 for i in range(10)}
        buckets_map["100"] = 0

        for r in results:
            if r.risk_score == 100:
                buckets_map["100"] += 1
            else:
                bucket_key = f"{(r.risk_score // 10) * 10}-{(r.risk_score // 10) * 10 + 9}"
                buckets_map[bucket_key] = buckets_map.get(bucket_key, 0) + 1

        buckets = [
            RiskDistributionBucket(range_label=k, count=v)
            for k, v in buckets_map.items()
        ]
        return RiskDistribution(buckets=buckets, total=len(results))
