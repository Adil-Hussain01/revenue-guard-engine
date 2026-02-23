"""
Epic 3: Finance Layer — Test Suite
Tests for invoice CRUD, double-entry bookkeeping, overpayment protection,
overdue detection, void reversal, and reconciliation mismatch reporting.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.main import app
from backend.api.finance_store import FinanceStore
from backend.api.qb_engine import get_store, get_rules, get_ledger
from backend.api.finance_models import Invoice, Payment
from backend.api.ledger_service import LedgerService
from backend.api.finance_business_rules import FinanceBusinessRules

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_store():
    """Provides a fresh FinanceStore with no seeded data."""
    store = FinanceStore(data_dir="/nonexistent/path")  # data_dir not found → empty store
    return store


@pytest.fixture
def override_store(clean_store):
    """Overrides app dependency to use a clean, isolated store."""
    ledger = LedgerService(clean_store)
    rules = FinanceBusinessRules(clean_store, ledger)

    app.dependency_overrides[get_store] = lambda: clean_store
    app.dependency_overrides[get_ledger] = lambda: ledger
    app.dependency_overrides[get_rules] = lambda: rules
    yield clean_store
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_invoice(override_store):
    """Inserts a known invoice into the clean store for test access."""
    inv = Invoice(
        invoice_id="INV-TEST001",
        order_id="ORD-TEST001",
        customer_id="CNT-TEST",
        line_items=[],
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("0.0"),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("0.0"),
        amount_due=Decimal("1000.00"),
        status="sent",
        issue_date=date(2025, 1, 1),
        due_date=date(2025, 2, 1),
        payment_terms="Net 30"
    )
    override_store.save_invoice(inv)
    return inv


# ---------------------------------------------------------------------------
# Test: Invoice Creation
# ---------------------------------------------------------------------------

def test_create_invoice(override_store):
    """POST /invoices creates a new invoice and returns 201 with correct fields."""
    payload = {
        "order_id": "ORD-NEW001",
        "customer_id": "CNT-001",
        "amount": "500.00"
    }
    res = client.post("/api/v1/finance/invoices", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["invoice_id"].startswith("INV-")
    assert data["order_id"] == "ORD-NEW001"
    assert data["status"] == "sent"
    assert float(data["amount_due"]) == float(data["total_amount"])


# ---------------------------------------------------------------------------
# Test: Double-Entry Balance
# ---------------------------------------------------------------------------

def test_double_entry_balance(override_store):
    """After creating an invoice, total debits must equal total credits across all accounts."""
    payload = {
        "order_id": "ORD-LEDGER001",
        "customer_id": "CNT-LEDGER",
        "amount": "2000.00"
    }
    client.post("/api/v1/finance/invoices", json=payload)

    ledger_res = client.get("/api/v1/finance/ledger")
    assert ledger_res.status_code == 200
    entries = ledger_res.json()

    # Verify the total debits across all entries equal total credits
    total_debit = sum(Decimal(e["debit"]) for e in entries)
    total_credit = sum(Decimal(e["credit"]) for e in entries)
    assert total_debit == total_credit, f"Balance broken: D={total_debit}, C={total_credit}"


# ---------------------------------------------------------------------------
# Test: Overpayment Rejection
# ---------------------------------------------------------------------------

def test_overpayment_rejection(seeded_invoice, override_store):
    """POST /payments with amount > amount_due returns 409 Conflict."""
    payload = {
        "invoice_id": "INV-TEST001",
        "amount": "9999.99",  # way more than the 1000.00 due
        "payment_method": "wire"
    }
    res = client.post("/api/v1/finance/payments", json=payload)
    assert res.status_code == 409
    assert "overpayment" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test: Successful Payment Updates Invoice Status
# ---------------------------------------------------------------------------

def test_payment_marks_invoice_paid(seeded_invoice, override_store):
    """POST /payments with full amount sets invoice status to 'paid'."""
    payload = {
        "invoice_id": "INV-TEST001",
        "amount": "1000.00",
        "payment_method": "ach"
    }
    res = client.post("/api/v1/finance/payments", json=payload)
    assert res.status_code == 201

    # Verify invoice status updated in store (via GET endpoint)
    inv_res = client.get("/api/v1/finance/invoices/INV-TEST001")
    assert inv_res.status_code == 200
    assert inv_res.json()["status"] == "paid"


# ---------------------------------------------------------------------------
# Test: Overdue Detection
# ---------------------------------------------------------------------------

def test_overdue_transition(override_store):
    """GET /invoices auto-detects overdue invoices past their due_date."""
    past_due = Invoice(
        invoice_id="INV-OVERDUE",
        order_id="ORD-OVERDUE",
        customer_id="CNT-LATE",
        line_items=[],
        subtotal=Decimal("500.00"),
        tax_amount=Decimal("0.0"),
        total_amount=Decimal("500.00"),
        amount_paid=Decimal("0.0"),
        amount_due=Decimal("500.00"),
        status="sent",
        issue_date=date(2024, 1, 1),
        due_date=date(2024, 2, 1),  # This is long in the past
        payment_terms="Net 30"
    )
    override_store.save_invoice(past_due)

    res = client.get("/api/v1/finance/invoices/INV-OVERDUE")
    assert res.status_code == 200
    assert res.json()["status"] == "overdue"


# ---------------------------------------------------------------------------
# Test: Void Invoice Reversal
# ---------------------------------------------------------------------------

def test_void_invoice_reversal(seeded_invoice, override_store):
    """POST /invoices/{id}/void should mark invoice as void and generate reversal ledger entries."""
    # First create the invoice ledger entries by creating via POST
    # (seeded_invoice was added directly to store — create fresh for ledger tracking)
    payload = {
        "order_id": "ORD-VOID001",
        "customer_id": "CNT-VOID",
        "amount": "750.00"
    }
    create_res = client.post("/api/v1/finance/invoices", json=payload)
    assert create_res.status_code == 201
    invoice_id = create_res.json()["invoice_id"]

    # Count ledger entries before void
    ledger_before = client.get("/api/v1/finance/ledger").json()

    # Void it
    void_res = client.post(f"/api/v1/finance/invoices/{invoice_id}/void")
    assert void_res.status_code == 200
    assert void_res.json()["status"] == "void"

    # Verify more ledger entries were added (the reversal pair)
    ledger_after = client.get("/api/v1/finance/ledger").json()
    assert len(ledger_after) > len(ledger_before)


# ---------------------------------------------------------------------------
# Test: Reconciliation Mismatches Endpoint
# ---------------------------------------------------------------------------

def test_reconciliation_endpoint(override_store):
    """GET /reconciliation/mismatches returns a valid list (can be empty on clean data)."""
    res = client.get("/api/v1/finance/reconciliation/mismatches")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
