"""
Epic 4 — Rule Registry & Concrete Rule Implementations

Provides the pluggable rule architecture:
  • ValidationRule — abstract base class every rule inherits
  • RuleRegistry   — central store for rule lookup
  • 12 concrete rule classes covering Pricing, Order↔Invoice, and Cross-System categories
  • build_default_registry() — factory that returns a fully‑loaded registry
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from backend.core.validation_models import RuleViolation, ValidationContext


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class ValidationRule(ABC):
    rule_id: str
    rule_name: str
    category: str           # "pricing" | "order_invoice" | "cross_system"
    severity: str           # "critical" | "high" | "medium" | "low"
    weight: int

    @abstractmethod
    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        """Return a RuleViolation if the rule fails, or None if it passes."""
        ...


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class RuleRegistry:
    def __init__(self):
        self._rules: dict[str, ValidationRule] = {}

    def register(self, rule: ValidationRule):
        self._rules[rule.rule_id] = rule

    def get_all(self) -> List[ValidationRule]:
        return list(self._rules.values())

    def get_by_category(self, category: str) -> List[ValidationRule]:
        return [r for r in self._rules.values() if r.category == category]

    def get(self, rule_id: str) -> Optional[ValidationRule]:
        return self._rules.get(rule_id)


# ═══════════════════════════════════════════════════════════════════════════
# Rule Set 1 — Pricing Integrity
# ═══════════════════════════════════════════════════════════════════════════

class PRC001_DiscountThreshold(ValidationRule):
    rule_id = "PRC-001"
    rule_name = "Discount Threshold"
    category = "pricing"
    severity = "critical"
    weight = 30

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        order = ctx.order
        if order.discount_pct > Decimal("15.0") and order.approval_status != "approved":
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                weight=self.weight,
                message=f"Discount {order.discount_pct}% exceeds 15% threshold without approval (status: {order.approval_status})",
                expected_value="approved",
                actual_value=order.approval_status,
            )
        return None


class PRC002_MarginProtection(ValidationRule):
    rule_id = "PRC-002"
    rule_name = "Margin Protection"
    category = "pricing"
    severity = "high"
    weight = 20

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        for item in ctx.order.line_items:
            # Use assumed cost = 90% of unit_price when cost data is absent
            assumed_cost = item.unit_price * Decimal("0.90")
            margin = (item.unit_price - assumed_cost) / item.unit_price if item.unit_price else Decimal("0")
            if margin < Decimal("0.10"):
                return RuleViolation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    weight=self.weight,
                    message=f"Low margin detected on product {item.product_id}: margin {margin:.2%}",
                    expected_value=">=10%",
                    actual_value=f"{margin:.2%}",
                )
        return None


class PRC003_PriceConsistency(ValidationRule):
    rule_id = "PRC-003"
    rule_name = "Price Consistency"
    category = "pricing"
    severity = "critical"
    weight = 30

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if not ctx.invoice:
            return None  # Can't check without invoice — OIC-001 handles that
        order_total = ctx.order.total_amount
        invoice_total = ctx.invoice.total_amount
        if order_total == Decimal("0"):
            return None
        drift = abs(order_total - invoice_total) / order_total
        if drift > Decimal("0.01"):
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                weight=self.weight,
                message=f"Price drift of {drift:.2%} between order ({order_total}) and invoice ({invoice_total})",
                expected_value=str(order_total),
                actual_value=str(invoice_total),
            )
        return None


class PRC004_BulkPriceValidation(ValidationRule):
    rule_id = "PRC-004"
    rule_name = "Bulk Price Validation"
    category = "pricing"
    severity = "medium"
    weight = 10

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        for item in ctx.order.line_items:
            if item.quantity > 100 and ctx.order.discount_pct == Decimal("0"):
                return RuleViolation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    weight=self.weight,
                    message=f"Bulk order ({item.quantity} units of {item.product_id}) has no bulk discount applied",
                    expected_value="discount > 0%",
                    actual_value="0%",
                )
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Rule Set 2 — Order → Invoice Consistency
# ═══════════════════════════════════════════════════════════════════════════

class OIC001_OrderInvoiceMapping(ValidationRule):
    rule_id = "OIC-001"
    rule_name = "Order-Invoice Mapping"
    category = "order_invoice"
    severity = "critical"
    weight = 30

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if not ctx.invoice and len(ctx.invoices) == 0:
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                weight=self.weight,
                message=f"Order {ctx.order.order_id} has no matching invoice in Finance system",
                expected_value=">=1 invoice",
                actual_value="0",
            )
        return None


class OIC002_AmountMatching(ValidationRule):
    rule_id = "OIC-002"
    rule_name = "Amount Matching"
    category = "order_invoice"
    severity = "critical"
    weight = 30

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if not ctx.invoice:
            return None
        diff = abs(ctx.order.total_amount - ctx.invoice.total_amount)
        if diff > Decimal("0.01"):
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                weight=self.weight,
                message=f"Amount mismatch: order={ctx.order.total_amount}, invoice={ctx.invoice.total_amount} (diff={diff})",
                expected_value=str(ctx.order.total_amount),
                actual_value=str(ctx.invoice.total_amount),
            )
        return None


class OIC003_DuplicateInvoice(ValidationRule):
    rule_id = "OIC-003"
    rule_name = "Duplicate Invoice"
    category = "order_invoice"
    severity = "high"
    weight = 20

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if len(ctx.invoices) > 1:
            ids = ", ".join(inv.invoice_id for inv in ctx.invoices)
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                weight=self.weight,
                message=f"Order {ctx.order.order_id} has {len(ctx.invoices)} invoices: [{ids}]",
                expected_value="1",
                actual_value=str(len(ctx.invoices)),
            )
        return None


class OIC004_PaymentCompleteness(ValidationRule):
    rule_id = "OIC-004"
    rule_name = "Payment Completeness"
    category = "order_invoice"
    severity = "high"
    weight = 20

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if not ctx.invoice:
            return None
        if ctx.invoice.status == "paid":
            total_paid = sum(p.amount for p in ctx.payments)
            if total_paid < ctx.invoice.total_amount:
                return RuleViolation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    weight=self.weight,
                    message=f"Invoice {ctx.invoice.invoice_id} marked 'paid' but payments sum ({total_paid}) < total ({ctx.invoice.total_amount})",
                    expected_value=str(ctx.invoice.total_amount),
                    actual_value=str(total_paid),
                )
        return None


class OIC005_StaleInvoice(ValidationRule):
    rule_id = "OIC-005"
    rule_name = "Stale Invoice"
    category = "order_invoice"
    severity = "medium"
    weight = 10

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if not ctx.invoice:
            return None
        if ctx.invoice.status not in ("paid", "void"):
            days_old = (date.today() - ctx.invoice.due_date).days
            if days_old > 60:
                return RuleViolation(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    weight=self.weight,
                    message=f"Invoice {ctx.invoice.invoice_id} is {days_old} days past due date",
                    expected_value="<= 60 days",
                    actual_value=f"{days_old} days",
                )
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Rule Set 3 — Cross-System Integrity
# ═══════════════════════════════════════════════════════════════════════════

class CSI001_GhostInvoice(ValidationRule):
    """
    Evaluated externally: checks for invoices referencing non‑existent CRM order.
    During per-order validation we cannot detect this (we start from an order).
    The reconciliation engine runs this separately across all invoices.
    For per-order context, this is a no-op.
    """
    rule_id = "CSI-001"
    rule_name = "Ghost Invoice"
    category = "cross_system"
    severity = "critical"
    weight = 30

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        # This rule is evaluated externally by the reconciliation engine
        # scanning invoices → checking CRM orders, not order → invoice.
        return None


class CSI002_StatusSynchronization(ValidationRule):
    rule_id = "CSI-002"
    rule_name = "Status Synchronization"
    category = "cross_system"
    severity = "high"
    weight = 20

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if not ctx.invoice:
            return None
        if ctx.order.order_status == "fulfilled" and ctx.invoice.status == "overdue":
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                weight=self.weight,
                message=f"CRM order is 'fulfilled' but invoice {ctx.invoice.invoice_id} is 'overdue'",
                expected_value="paid or sent",
                actual_value="overdue",
            )
        return None


class CSI003_LedgerBalance(ValidationRule):
    """
    Checks that for the related invoice, all ledger entries sum to balanced debits/credits.
    """
    rule_id = "CSI-003"
    rule_name = "Ledger Balance"
    category = "cross_system"
    severity = "critical"
    weight = 30

    def evaluate(self, ctx: ValidationContext) -> Optional[RuleViolation]:
        if not ctx.ledger_entries:
            return None
        total_debit = sum(e.debit for e in ctx.ledger_entries)
        total_credit = sum(e.credit for e in ctx.ledger_entries)
        if abs(total_debit - total_credit) > Decimal("0.01"):
            return RuleViolation(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                weight=self.weight,
                message=f"Ledger imbalance: debits={total_debit}, credits={total_credit}",
                expected_value=str(total_debit),
                actual_value=str(total_credit),
            )
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════════════════

def build_default_registry() -> RuleRegistry:
    """Instantiates all 12 rules and returns a fully-loaded registry."""
    registry = RuleRegistry()
    for rule_cls in [
        PRC001_DiscountThreshold,
        PRC002_MarginProtection,
        PRC003_PriceConsistency,
        PRC004_BulkPriceValidation,
        OIC001_OrderInvoiceMapping,
        OIC002_AmountMatching,
        OIC003_DuplicateInvoice,
        OIC004_PaymentCompleteness,
        OIC005_StaleInvoice,
        CSI001_GhostInvoice,
        CSI002_StatusSynchronization,
        CSI003_LedgerBalance,
    ]:
        registry.register(rule_cls())
    return registry
