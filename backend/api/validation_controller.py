"""
Epic 4 — Validation Controller

FastAPI router exposing the validation/reconciliation engine to REST clients.
Prefix: /api/v1/validation/
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from backend.api.crm_store import CRMStore
from backend.api.ghl_connector import get_store as get_crm_store
from backend.api.finance_store import FinanceStore
from backend.api.qb_engine import get_store as get_finance_store
from backend.core.audit_logger import AuditLogger
from backend.core.audit_store import AuditStore
from backend.core.reconciliation_engine import ReconciliationEngine
from backend.core.validation_models import (
    ValidationResult,
    ValidationStatistics,
    RiskDistribution,
)

validation_router = APIRouter(
    prefix="/api/v1/validation",
    tags=["Validation & Risk Scoring Engine"],
)

# ---------------------------------------------------------------------------
# Singleton engine (created lazily so store DI works)
# ---------------------------------------------------------------------------

_engine: Optional[ReconciliationEngine] = None


def _get_engine() -> ReconciliationEngine:
    global _engine
    if _engine is None:
        crm = get_crm_store()
        fin = get_finance_store()
        audit = AuditLogger(AuditStore())
        _engine = ReconciliationEngine(crm, fin, audit)
    return _engine


def get_engine() -> ReconciliationEngine:
    return _get_engine()


def reset_engine():
    """Testing hook to allow DI override."""
    global _engine
    _engine = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@validation_router.post(
    "/validate/transaction/{order_id}",
    response_model=ValidationResult,
)
def validate_transaction(
    order_id: str,
    engine: ReconciliationEngine = Depends(get_engine),
):
    """Validate a single CRM order against the Finance system."""
    return engine.reconcile_transaction(order_id)


@validation_router.post(
    "/validate/batch",
    response_model=List[ValidationResult],
)
def validate_batch(
    order_ids: List[str],
    engine: ReconciliationEngine = Depends(get_engine),
):
    """Validate a batch of order IDs."""
    return engine.reconcile_batch(order_ids)


@validation_router.post(
    "/run-full-scan",
    response_model=List[ValidationResult],
)
def run_full_scan(
    engine: ReconciliationEngine = Depends(get_engine),
):
    """Trigger validation across ALL orders in the CRM store."""
    return engine.reconcile_all()


@validation_router.get(
    "/results",
    response_model=List[ValidationResult],
)
def list_results(
    classification: Optional[str] = Query(None, description="Filter by risk_classification (safe|monitor|critical)"),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    engine: ReconciliationEngine = Depends(get_engine),
):
    """List all validation results with optional filters."""
    results = engine.get_all_results()
    if classification:
        results = [r for r in results if r.risk_classification == classification]
    if min_score is not None:
        results = [r for r in results if r.risk_score >= min_score]
    if max_score is not None:
        results = [r for r in results if r.risk_score <= max_score]
    return results


@validation_router.get(
    "/results/{order_id}",
    response_model=ValidationResult,
)
def get_result(
    order_id: str,
    engine: ReconciliationEngine = Depends(get_engine),
):
    """Get validation result for a specific order."""
    result = engine.get_result(order_id)
    if not result:
        raise HTTPException(404, detail=f"No validation result found for order {order_id}")
    return result


@validation_router.get(
    "/statistics",
    response_model=ValidationStatistics,
)
def get_statistics(
    engine: ReconciliationEngine = Depends(get_engine),
):
    """Aggregated validation statistics."""
    return engine.get_statistics()


@validation_router.get(
    "/risk-distribution",
    response_model=RiskDistribution,
)
def get_risk_distribution(
    engine: ReconciliationEngine = Depends(get_engine),
):
    """Risk score histogram for charting."""
    return engine.get_risk_distribution()
