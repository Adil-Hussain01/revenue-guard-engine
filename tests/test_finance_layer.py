import pytest
from decimal import Decimal
from datetime import date, timedelta

from backend.api.finance_models import Invoice, Payment
from backend.api.finance_store import FinanceStore
from backend.api.ledger_service import LedgerService
from backend.api.finance_business_rules import FinanceBusinessRules

@pytest.fixture
def empty_store():
    return FinanceStore(data_dir="empty_path")

@pytest.fixture
def test_invoice():
    return Invoice(
        invoice_id="INV-TEST-001",
        order_id="ORD-TEST-001",
        customer_id="CUST-01",
        subtotal=Decimal("1000.0"),
        total_amount=Decimal("1000.0"),
        amount_paid=Decimal("0.0"),
        amount_due=Decimal("1000.0"),
        status="sent",
        issue_date=date.today() - timedelta(days=5),
        due_date=date.today() + timedelta(days=25)
    )

def test_double_entry_balance(empty_store, test_invoice):
    """After any transaction, total debits MUST equal total credits system-wide."""
    ledger = LedgerService(empty_store)
    
    empty_store.save_invoice(test_invoice)
    ledger.record_invoice_creation(test_invoice)
    
    entries = empty_store.list_ledger()
    assert len(entries) == 2
    
    total_debits = sum(e.debit for e in entries)
    total_credits = sum(e.credit for e in entries)
    assert total_debits == total_credits
    assert total_debits == Decimal("1000.0")

def test_overpayment_rejection(empty_store, test_invoice):
    """Paying more than amount_due raises ValueError."""
    ledger = LedgerService(empty_store)
    rules = FinanceBusinessRules(empty_store, ledger)
    
    empty_store.save_invoice(test_invoice)
    
    payment = Payment(
        payment_id="PAY-TEST-001",
        invoice_id="INV-TEST-001",
        amount=Decimal("1200.0"),
        payment_method="credit_card",
        payment_date=date.today(),
        status="completed"
    )
    
    with pytest.raises(ValueError, match="Overpayment exception"):
        rules.apply_payment(payment)

def test_overdue_transition(empty_store, test_invoice):
    """Invoices past due_date auto transition to overdue."""
    ledger = LedgerService(empty_store)
    rules = FinanceBusinessRules(empty_store, ledger)
    
    # Make it past due
    test_invoice.due_date = date.today() - timedelta(days=1)
    empty_store.save_invoice(test_invoice)
    
    assert test_invoice.status == "sent"
    rules.evaluate_overdue_invoices()
    
    inv = empty_store.get_invoice("INV-TEST-001")
    assert inv.status == "overdue"

def test_void_reversal(empty_store, test_invoice):
    """Voiding an invoice reverses all active ledger entries exactly."""
    ledger = LedgerService(empty_store)
    
    empty_store.save_invoice(test_invoice)
    ledger.record_invoice_creation(test_invoice)
    
    pre_void_len = len(empty_store.list_ledger())
    
    ledger.reverse_invoice(test_invoice.invoice_id)
    post_void_len = len(empty_store.list_ledger())
    
    # Needs 2 original entries + 2 reversal entries = 4
    assert post_void_len == pre_void_len * 2
    
    balances = ledger.get_account_balances()
    assert balances["accounts_receivable"] == Decimal("0.0")
    assert balances["revenue"] == Decimal("0.0")
