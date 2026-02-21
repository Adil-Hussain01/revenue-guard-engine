"""
Epic 4 — Validation Engine Test Suite

Covers:
  • Individual rule evaluation
  • Risk score calculation & classification
  • Clean transaction validation
  • Batch validation
  • Full-scan endpoint
"""
import pytest
from datetime import datetime, date, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.main import app
from backend.api.crm_store import CRMStore
from backend.api.crm_models import Order, LineItem
from backend.api.finance_store import FinanceStore
from backend.api.finance_models import Invoice
from backend.api.crm_simulator import get_store as get_crm_store
from backend.api.finance_simulator import get_store as get_finance_store
from backend.api.validation_controller import get_engine, reset_engine
from backend.core.reconciliation_engine import ReconciliationEngine
from backend.core.validation_models import ValidationContext, RuleViolation
from backend.core.rule_registry import (
    PRC001_DiscountThreshold,
    OIC001_OrderInvoiceMapping,
    OIC002_AmountMatching,
)
from backend.core import risk_scoring_engine

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from backend.api.crm_models import Contact, Deal, Opportunity

def _make_contact(**overrides) -> Contact:
    defaults = dict(
        contact_id="CNT-T",
        name="Test User",
        email="test@example.com",
        company="Test Co",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    defaults.update(overrides)
    return Contact(**defaults)

def _make_deal(**overrides) -> Deal:
    defaults = dict(
        deal_id="DEAL-T",
        contact_id="CNT-T",
        stage="closed_won",
        value=Decimal("1000"),
        assigned_to="Sales Rep",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    defaults.update(overrides)
    return Deal(**defaults)

def _make_opportunity(**overrides) -> Opportunity:
    defaults = dict(
        opportunity_id="OPP-T",
        deal_id="DEAL-T",
        contact_id="CNT-T",
        status="won",
        expected_close_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    defaults.update(overrides)
    return Opportunity(**defaults)

def _make_order(**overrides) -> Order:
    defaults = dict(
        order_id="ORD-T001",
        opportunity_id="OPP-T",
        contact_id="CNT-T",
        line_items=[
            LineItem(product_id="P1", product_name="Widget", quantity=2, unit_price=Decimal("500"), total_price=Decimal("1000"))
        ],
        subtotal=Decimal("1000"),
        discount_pct=Decimal("0"),
        discount_amount=Decimal("0"),
        total_amount=Decimal("1000"),
        approval_status="pending",
        order_status="confirmed",
        order_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return Order(**defaults)


from backend.api.finance_models import Invoice, Payment

def _make_payment(**overrides) -> Payment:
    defaults = dict(
        payment_id="PAY-T",
        invoice_id="INV-T001",
        customer_id="CNT-T",
        amount=Decimal("1000"),
        payment_date=datetime(2025, 6, 15, tzinfo=timezone.utc),
        payment_method="credit_card",
        status="completed",
        reference_number="REF-BATCH"
    )
    defaults.update(overrides)
    return Payment(**defaults)

def _make_invoice(**overrides) -> Invoice:
    defaults = dict(
        invoice_id="INV-T001",
        order_id="ORD-T001",
        customer_id="CNT-T",
        line_items=[],
        subtotal=Decimal("1000"),
        tax_amount=Decimal("0"),
        total_amount=Decimal("1000"),
        amount_paid=Decimal("1000"),
        amount_due=Decimal("0"),
        status="paid",
        issue_date=date(2025, 6, 1),
        due_date=date(2025, 7, 1),
        payment_terms="Net 30",
    )
    defaults.update(overrides)
    return Invoice(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_stores():
    """Fresh CRM + Finance stores with no seeded data."""
    crm = CRMStore(data_dir="/nonexistent")
    fin = FinanceStore(data_dir="/nonexistent")
    return crm, fin


@pytest.fixture
def override_engine(clean_stores):
    """Override app DI to use isolated stores."""
    crm, fin = clean_stores
    engine = ReconciliationEngine(crm, fin, audit_logger=None)

    app.dependency_overrides[get_crm_store] = lambda: crm
    app.dependency_overrides[get_finance_store] = lambda: fin
    app.dependency_overrides[get_engine] = lambda: engine

    yield engine
    app.dependency_overrides.clear()
    reset_engine()


# ---------------------------------------------------------------------------
# Test: PRC-001 — Unauthorized Discount
# ---------------------------------------------------------------------------

def test_prc001_unauthorized_discount():
    """20% discount without approval → critical violation."""
    order = _make_order(discount_pct=Decimal("20"), approval_status="pending")
    ctx = ValidationContext(order=order)
    rule = PRC001_DiscountThreshold()
    result = rule.evaluate(ctx)
    assert result is not None
    assert result.rule_id == "PRC-001"
    assert result.severity == "critical"


# ---------------------------------------------------------------------------
# Test: OIC-001 — Missing Invoice
# ---------------------------------------------------------------------------

def test_oic001_missing_invoice():
    """Order with no invoice → critical violation."""
    order = _make_order()
    ctx = ValidationContext(order=order, invoice=None, invoices=[])
    rule = OIC001_OrderInvoiceMapping()
    result = rule.evaluate(ctx)
    assert result is not None
    assert result.rule_id == "OIC-001"
    assert result.severity == "critical"


# ---------------------------------------------------------------------------
# Test: OIC-002 — Amount Mismatch
# ---------------------------------------------------------------------------

def test_oic002_amount_mismatch():
    """Invoice total ≠ order total → critical violation with drift."""
    order = _make_order(total_amount=Decimal("1000"))
    invoice = _make_invoice(total_amount=Decimal("950"))
    ctx = ValidationContext(order=order, invoice=invoice, invoices=[invoice])
    rule = OIC002_AmountMatching()
    result = rule.evaluate(ctx)
    assert result is not None
    assert result.rule_id == "OIC-002"
    assert "mismatch" in result.message.lower()


# ---------------------------------------------------------------------------
# Test: Risk Score Calculation
# ---------------------------------------------------------------------------

def test_risk_score_calculation():
    """2 Critical (30 each) + 1 High (20) = min(100, 80) = 80."""
    violations = [
        RuleViolation(rule_id="A", rule_name="A", severity="critical", weight=30, message=""),
        RuleViolation(rule_id="B", rule_name="B", severity="critical", weight=30, message=""),
        RuleViolation(rule_id="C", rule_name="C", severity="high",     weight=20, message=""),
    ]
    score = risk_scoring_engine.calculate_score(violations)
    assert score == 80


# ---------------------------------------------------------------------------
# Test: Risk Classification
# ---------------------------------------------------------------------------

def test_risk_classification():
    """Score 75 → critical, score 25 → safe."""
    assert risk_scoring_engine.classify_risk(75) == "critical"
    assert risk_scoring_engine.classify_risk(25) == "safe"
    assert risk_scoring_engine.classify_risk(50) == "monitor"


# ---------------------------------------------------------------------------
# Test: Clean Transaction
# ---------------------------------------------------------------------------

def test_clean_transaction(override_engine, clean_stores):
    """Order with matching invoice and no issues → score 0, safe."""
    crm, fin = clean_stores
    contact = _make_contact()
    deal = _make_deal(contact_id=contact.contact_id)
    opp = _make_opportunity(contact_id=contact.contact_id, deal_id=deal.deal_id)
    order = _make_order(contact_id=contact.contact_id, opportunity_id=opp.opportunity_id)
    invoice = _make_invoice(customer_id=contact.contact_id, order_id=order.order_id)
    
    crm.add_contact(contact)
    crm.add_deal(deal)
    crm.add_opportunity(opp)
    crm.add_order(order)
    
    fin.save_invoice(invoice)
    fin.save_payment(_make_payment(invoice_id=invoice.invoice_id, customer_id=contact.contact_id, amount=invoice.total_amount))
    
    result = override_engine.reconcile_transaction(order.order_id)
    assert result.risk_score == 0
    assert result.risk_classification == "safe"
    assert result.violations == []


# ---------------------------------------------------------------------------
# Test: Batch Validation via API
# ---------------------------------------------------------------------------

def test_batch_validation(override_engine, clean_stores):
    """POST /validate/batch processes a list of order IDs."""
    crm, fin = clean_stores
    contact = _make_contact()
    deal = _make_deal(contact_id=contact.contact_id)
    crm.add_contact(contact)
    crm.add_deal(deal)
    for i in range(3):
        oid = f"ORD-BATCH{i}"
        opp_id = f"OPP-BATCH{i}"
        opp = _make_opportunity(opportunity_id=opp_id, contact_id=contact.contact_id, deal_id=deal.deal_id)
        crm.add_opportunity(opp)
        crm.add_order(_make_order(order_id=oid, contact_id=contact.contact_id, opportunity_id=opp_id))
        inv = _make_invoice(invoice_id=f"INV-BATCH{i}", order_id=oid, customer_id=contact.contact_id)
        fin.save_invoice(inv)
        fin.save_payment(_make_payment(invoice_id=inv.invoice_id, customer_id=contact.contact_id, amount=inv.total_amount))

    res = client.post("/api/v1/validation/validate/batch", json=["ORD-BATCH0", "ORD-BATCH1", "ORD-BATCH2"])
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    assert all(r["risk_classification"] == "safe" for r in data)


# ---------------------------------------------------------------------------
# Test: Full Scan via API
# ---------------------------------------------------------------------------

def test_full_scan_endpoint(override_engine, clean_stores):
    """POST /run-full-scan validates all CRM orders."""
    crm, fin = clean_stores
    contact = _make_contact()
    deal = _make_deal(contact_id=contact.contact_id)
    crm.add_contact(contact)
    crm.add_deal(deal)
    for i in range(5):
        oid = f"ORD-SCAN{i}"
        opp_id = f"OPP-SCAN{i}"
        opp = _make_opportunity(opportunity_id=opp_id, contact_id=contact.contact_id, deal_id=deal.deal_id)
        crm.add_opportunity(opp)
        crm.add_order(_make_order(order_id=oid, contact_id=contact.contact_id, opportunity_id=opp_id))
        inv = _make_invoice(invoice_id=f"INV-SCAN{i}", order_id=oid, customer_id=contact.contact_id)
        fin.save_invoice(inv)
        fin.save_payment(_make_payment(invoice_id=inv.invoice_id, customer_id=contact.contact_id, amount=inv.total_amount))

    res = client.post("/api/v1/validation/run-full-scan")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
