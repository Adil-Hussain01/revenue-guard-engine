"""
Epic 4 — Validation & Risk Scoring Engine: Data Models

Defines the Pydantic schemas used across the rule engine, reconciliation
orchestrator, and validation API endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from decimal import Decimal

from backend.api.crm_models import Order
from backend.api.finance_models import Invoice, Payment, LedgerEntry


# ---------------------------------------------------------------------------
# Rule Evaluation
# ---------------------------------------------------------------------------

class RuleViolation(BaseModel):
    """A single failed or warned rule evaluation."""
    rule_id: str                            # e.g. "PRC-001"
    rule_name: str
    severity: str                           # "critical" | "high" | "medium" | "low"
    message: str                            # Human-readable explanation
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    weight: int


class ValidationContext(BaseModel):
    """
    Carrier DTO that bundles all data the rule engine needs to evaluate
    a single transaction.
    """
    order: Order
    invoice: Optional[Invoice] = None
    invoices: List[Invoice] = Field(default_factory=list)
    payments: List[Payment] = Field(default_factory=list)
    ledger_entries: List[LedgerEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation Result
# ---------------------------------------------------------------------------

class ValidationResult(BaseModel):
    """Per-order validation outcome."""
    order_id: str
    risk_score: int = 0                     # 0–100
    risk_classification: str = "safe"       # "safe" | "monitor" | "critical"
    rules_evaluated: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    rules_warned: int = 0
    violations: List[RuleViolation] = Field(default_factory=list)
    validated_at: datetime


# ---------------------------------------------------------------------------
# API Response Models
# ---------------------------------------------------------------------------

class ValidationStatistics(BaseModel):
    """Aggregated metrics returned by GET /statistics."""
    total_transactions: int
    total_validated: int
    safe_count: int
    monitor_count: int
    critical_count: int
    average_risk_score: float
    top_violated_rules: List[Dict[str, Any]] = Field(default_factory=list)


class RiskDistributionBucket(BaseModel):
    range_label: str            # e.g. "0-10", "11-20", …
    count: int


class RiskDistribution(BaseModel):
    """Histogram data returned by GET /risk-distribution."""
    buckets: List[RiskDistributionBucket] = Field(default_factory=list)
    total: int = 0
