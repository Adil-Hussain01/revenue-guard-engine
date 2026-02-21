import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from backend.api.finance_models import Invoice, Payment, LedgerEntry
from backend.api.finance_store import FinanceStore

class LedgerService:
    """Manages double-entry bookkeeping logic."""
    def __init__(self, store: FinanceStore):
        self.store = store

    def _generate_id(self) -> str:
        # Simplistic ID generation logic
        return f"LEDG-{uuid.uuid4().hex[:8].upper()}"

    def record_invoice_creation(self, invoice: Invoice):
        """Accounts Receivable (Debit) vs Revenue (Credit)."""
        now = datetime.now()
        
        ar_entry = LedgerEntry(
            entry_id=self._generate_id(),
            invoice_id=invoice.invoice_id,
            account="accounts_receivable",
            debit=invoice.total_amount,
            credit=Decimal("0.0"),
            description=f"Invoice {invoice.invoice_id} Created - AR",
            posted_date=now
        )
        
        rev_entry = LedgerEntry(
            entry_id=self._generate_id(),
            invoice_id=invoice.invoice_id,
            account="revenue",
            debit=Decimal("0.0"),
            credit=invoice.total_amount,
            description=f"Invoice {invoice.invoice_id} Created - Revenue",
            posted_date=now
        )
        
        self.store.save_ledger_entry(ar_entry)
        self.store.save_ledger_entry(rev_entry)

    def record_payment_receipt(self, payment: Payment):
        """Cash (Debit) vs Accounts Receivable (Credit)."""
        now = datetime.now()
        
        cash_entry = LedgerEntry(
            entry_id=self._generate_id(),
            invoice_id=payment.invoice_id,
            payment_id=payment.payment_id,
            account="cash",
            debit=payment.amount,
            credit=Decimal("0.0"),
            description=f"Payment {payment.payment_id} Received - Cash",
            posted_date=now
        )
        
        ar_entry = LedgerEntry(
            entry_id=self._generate_id(),
            invoice_id=payment.invoice_id,
            payment_id=payment.payment_id,
            account="accounts_receivable",
            debit=Decimal("0.0"),
            credit=payment.amount,
            description=f"Payment {payment.payment_id} Received - AR Reduction",
            posted_date=now
        )
        
        self.store.save_ledger_entry(cash_entry)
        self.store.save_ledger_entry(ar_entry)

    def reverse_invoice(self, invoice_id: str):
        """Reverses all ledger entries associated with this invoice (Void)."""
        target_entries = [e for e in self.store.list_ledger() if e.invoice_id == invoice_id]
        now = datetime.now()
        
        for entry in target_entries:
            # Create the exact opposite
            rev_entry = LedgerEntry(
                entry_id=self._generate_id(),
                invoice_id=invoice_id,
                payment_id=entry.payment_id,
                account=entry.account,
                debit=entry.credit, # swap
                credit=entry.debit, # swap
                description=f"Reversal for {entry.entry_id} (Void/Refund)",
                posted_date=now
            )
            self.store.save_ledger_entry(rev_entry)

    def get_account_balances(self) -> Dict[str, Decimal]:
        """Calculates current global balances."""
        balances = {
            "accounts_receivable": Decimal("0.0"),
            "revenue": Decimal("0.0"),
            "cash": Decimal("0.0"),
            "refunds": Decimal("0.0")
        }
        
        for entry in self.store.list_ledger():
            if entry.account not in balances:
                balances[entry.account] = Decimal("0.0")
            
            # Normal balances: 
            # Assets (AR, Cash) increase via Debit, decrease via Credit.
            # Revenue/Equity increase via Credit, decrease via Debit.
            if entry.account in ["accounts_receivable", "cash", "refunds"]:
                balances[entry.account] += (entry.debit - entry.credit)
            elif entry.account in ["revenue"]:
                balances[entry.account] += (entry.credit - entry.debit)

        return balances
