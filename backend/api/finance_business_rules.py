from datetime import date
from pydantic import ValidationError
from typing import List

from backend.api.finance_models import Invoice, Payment, MismatchRecord
from backend.api.finance_store import FinanceStore
from backend.api.ledger_service import LedgerService

class FinanceBusinessRules:
    """Applies strict limits and logic validation for finance operations."""
    def __init__(self, store: FinanceStore, ledger: LedgerService):
        self.store = store
        self.ledger = ledger

    def evaluate_overdue_invoices(self):
        """Scans all invoices. If past due_date AND amount_due > 0, status -> overdue."""
        today = date.today()
        for inv in self.store.list_invoices():
            if inv.status not in ["paid", "void", "draft"]:
                if inv.due_date < today and inv.amount_due > 0:
                    inv.status = "overdue"

    def apply_payment(self, payment: Payment) -> Invoice:
        """Applies a payment against an invoice. Raises ValueError if cap exceeded."""
        invoice = self.store.get_invoice(payment.invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        if invoice.status == "void":
            raise ValueError("Cannot pay voided invoice")

        if payment.amount > invoice.amount_due:
            raise ValueError(f"Overpayment exception: Attempted {payment.amount}, due {invoice.amount_due}")

        invoice.amount_paid += payment.amount
        invoice.amount_due -= payment.amount
        
        if invoice.amount_due == 0:
            invoice.status = "paid"
        else:
            invoice.status = "partial"

        self.store.save_invoice(invoice)
        self.store.save_payment(payment)
        self.ledger.record_payment_receipt(payment)
        
        return invoice

    def detect_mismatches(self, crm_orders: List[dict] = None) -> List[MismatchRecord]:
        """
        Internal drift detection checking generated anomalies.
        Since we rely on seeded data for ghost info, if `crm_orders` isn't provided we inspect the store limits.
        """
        mismatches = []
        
        if crm_orders:
            order_index = {o["order_id"]: o for o in crm_orders}
            
            # Check for Ghost Invoices, Amount Drift, and Status Conflicts
            for inv in self.store.list_invoices():
                if inv.order_id not in order_index:
                    mismatches.append(MismatchRecord(
                        mismatch_type="ghost_invoice",
                        entity_id=inv.invoice_id,
                        description="Invoice exists without matching CRM order",
                        actual_value=inv.order_id
                    ))
                else:
                    order = order_index[inv.order_id]
                    import decimal
                    order_amt = decimal.Decimal(str(order["total_amount"]))
                    if order_amt != inv.total_amount:
                        mismatches.append(MismatchRecord(
                            mismatch_type="amount_drift",
                            entity_id=inv.invoice_id,
                            description="Invoice amount does not match CRM order amount",
                            expected_value=str(order_amt),
                            actual_value=str(inv.total_amount)
                        ))
                        
            # Check for Duplicate Invoices
            order_invoice_refs = {}
            for inv in self.store.list_invoices():
                order_invoice_refs.setdefault(inv.order_id, []).append(inv.invoice_id)
            
            for ord_id, inv_ids in order_invoice_refs.items():
                if len(inv_ids) > 1:
                    mismatches.append(MismatchRecord(
                        mismatch_type="duplicate_invoice",
                        entity_id=ord_id,
                        description="Order ID mapped to multiple distinct invoices",
                        actual_value=",".join(inv_ids)
                    ))

        return mismatches
