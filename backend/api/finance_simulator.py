import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict

from fastapi import APIRouter, HTTPException, Depends, status

from backend.api.finance_models import (
    Invoice, Payment, LedgerEntry, InvoiceCreateRequest, InvoiceUpdateRequest,
    PaymentCreateRequest, ReconciliationReport, MismatchRecord
)
from backend.api.finance_store import FinanceStore
from backend.api.ledger_service import LedgerService
from backend.api.finance_business_rules import FinanceBusinessRules

finance_router = APIRouter(prefix="/api/v1/finance", tags=["Finance System (QuickBooks Simulator)"])

# ---------------------------------------------------------
# Dependency Injection / Global State Mock
# ---------------------------------------------------------
_store = FinanceStore()
_ledger = LedgerService(_store)
_rules = FinanceBusinessRules(_store, _ledger)

def get_store() -> FinanceStore:
    return _store

def get_rules() -> FinanceBusinessRules:
    return _rules

def get_ledger() -> LedgerService:
    return _ledger

# ---------------------------------------------------------
# Invoice Endpoints
# ---------------------------------------------------------
@finance_router.get("/invoices", response_model=List[Invoice])
def list_invoices(store: FinanceStore = Depends(get_store), rules: FinanceBusinessRules = Depends(get_rules)):
    """List all invoices. Auto-triggers overdue detection."""
    rules.evaluate_overdue_invoices()
    return store.list_invoices()

@finance_router.get("/invoices/{invoice_id}", response_model=Invoice)
def get_invoice(invoice_id: str, store: FinanceStore = Depends(get_store), rules: FinanceBusinessRules = Depends(get_rules)):
    rules.evaluate_overdue_invoices()
    inv = store.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv

@finance_router.post("/invoices", response_model=Invoice, status_code=status.HTTP_201_CREATED)
def create_invoice(req: InvoiceCreateRequest, store: FinanceStore = Depends(get_store), ledger: LedgerService = Depends(get_ledger)):
    """Creates a new invoice and triggers Accounts Receivable / Revenue double entries."""
    inv = Invoice(
        invoice_id=f"INV-{uuid.uuid4().hex[:6].upper()}",
        order_id=req.order_id,
        customer_id=req.customer_id,
        subtotal=req.amount,
        total_amount=req.amount,
        amount_paid=Decimal("0.0"),
        amount_due=req.amount,
        status="sent",
        issue_date=req.issue_date or date.today(),
        due_date=(req.issue_date or date.today())
    )
    store.save_invoice(inv)
    ledger.record_invoice_creation(inv)
    return inv

@finance_router.put("/invoices/{invoice_id}", response_model=Invoice)
def update_invoice(invoice_id: str, req: InvoiceUpdateRequest, store: FinanceStore = Depends(get_store)):
    inv = store.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if req.status:
        inv.status = req.status
    if req.total_amount is not None:
        inv.total_amount = req.total_amount
        inv.amount_due = inv.total_amount - inv.amount_paid
    if req.amount_paid is not None:
        inv.amount_paid = req.amount_paid
        inv.amount_due = inv.total_amount - inv.amount_paid
        
    store.save_invoice(inv)
    return inv

@finance_router.post("/invoices/{invoice_id}/send", response_model=Invoice)
def send_invoice(invoice_id: str, store: FinanceStore = Depends(get_store)):
    inv = store.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.status == "draft":
        inv.status = "sent"
        store.save_invoice(inv)
    return inv

@finance_router.post("/invoices/{invoice_id}/void", response_model=Invoice)
def void_invoice(invoice_id: str, store: FinanceStore = Depends(get_store), ledger: LedgerService = Depends(get_ledger)):
    """Voids an invoice and automatically reverses all attached ledger records."""
    inv = store.get_invoice(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if inv.status != "void":
        inv.status = "void"
        store.save_invoice(inv)
        ledger.reverse_invoice(invoice_id)
    return inv

# ---------------------------------------------------------
# Payment Endpoints
# ---------------------------------------------------------
@finance_router.get("/payments", response_model=List[Payment])
def list_payments(store: FinanceStore = Depends(get_store)):
    return store.list_payments()

@finance_router.post("/payments", response_model=Payment, status_code=status.HTTP_201_CREATED)
def record_payment(req: PaymentCreateRequest, rules: FinanceBusinessRules = Depends(get_rules)):
    """Records a payment, preventing overpayment and generating Cash/AR ledger entries."""
    pay = Payment(
        payment_id=f"PAY-{uuid.uuid4().hex[:6].upper()}",
        invoice_id=req.invoice_id,
        amount=req.amount,
        payment_method=req.payment_method,
        payment_date=datetime.now(),
        status="completed"
    )
    try:
        rules.apply_payment(pay)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return pay

# ---------------------------------------------------------
# Ledger & Reconciliation Endpoints
# ---------------------------------------------------------
@finance_router.get("/ledger", response_model=List[LedgerEntry])
def list_ledger(store: FinanceStore = Depends(get_store)):
    return store.list_ledger()

@finance_router.get("/ledger/balance", response_model=Dict[str, Decimal])
def get_ledger_balance(ledger: LedgerService = Depends(get_ledger)):
    """Returns the globally aggregated double-entry account balances."""
    return ledger.get_account_balances()

@finance_router.get("/reconciliation/mismatches", response_model=List[MismatchRecord])
def list_mismatches(rules: FinanceBusinessRules = Depends(get_rules)):
    """Returns detected status drifts internally generated or flagged against CRM (mocked CRM context)."""
    # For now, detects internal inconsistencies (Ghost Invoices, Duplicates).
    # Actual cross-reference requires Epic 4 engine to inject CRM orders.
    return rules.detect_mismatches()
