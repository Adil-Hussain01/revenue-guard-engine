import os
import json
from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal

from backend.api.finance_models import Invoice, Payment, LedgerEntry

class FinanceStore:
    """
    In-memory mock data store for QuickBooks API simulation.
    Seeds itself from generated_data/ upon initialization.
    """
    def __init__(self, data_dir: str = "generated_data"):
        self.data_dir = data_dir
        self.invoices: Dict[str, Invoice] = {}
        self.payments: Dict[str, Payment] = {}
        self.ledger: Dict[str, LedgerEntry] = {}
        
        # Load Epic 1 Seed Data if it exists
        self._load_seed_data()

    @staticmethod
    def _parse_date(value: str):
        """Strips the time component from an Epic-1 datetime string, returning a date."""
        # Handles both 'YYYY-MM-DD HH:MM:SS.ffffff' and 'YYYY-MM-DD' formats.
        return date.fromisoformat(value.split(" ")[0].split("T")[0])

    def _load_seed_data(self):
        """Loads seeded JSON generated from Data Simulation epic."""
        self.invoices.clear()
        self.payments.clear()
        self.ledger.clear()

        invoices_path = os.path.join(self.data_dir, "invoices.json")
        payments_path = os.path.join(self.data_dir, "payments.json")
        ledger_path = os.path.join(self.data_dir, "ledger_entries.json")
        orders_path = os.path.join(self.data_dir, "orders.json")

        # In realistic mapping we need customer_id from orders which Epic 1 outputted
        order_to_customer = {}
        if os.path.exists(orders_path):
            with open(orders_path, "r") as f:
                orders_data = json.load(f)
                for o in orders_data:
                    order_to_customer[o["order_id"]] = o["contact_id"]

        if os.path.exists(invoices_path):
            with open(invoices_path, "r") as f:
                inv_data = json.load(f)
                for item in inv_data:
                    # Mapping epic 1 simplified invoices to QuickBooks comprehensive models
                    # Using Decimal for precise accounting math
                    amount_due = Decimal(str(item.get("amount_due", 0)))
                    amount_paid = Decimal(str(item.get("amount_paid", 0)))

                    # Normalize Epic 1 statuses to Finance Literal values
                    VALID_STATUSES = {"draft", "sent", "partial", "paid", "overdue", "void"}
                    raw_status = item.get("status", "sent")
                    normalized_status = raw_status if raw_status in VALID_STATUSES else "sent"

                    inv = Invoice(
                        invoice_id=item["invoice_id"],
                        order_id=item["order_id"],
                        customer_id=order_to_customer.get(item["order_id"], "UNKNOWN"),
                        subtotal=amount_due, # simplified
                        total_amount=amount_due,
                        amount_paid=amount_paid,
                        amount_due=amount_due - amount_paid,
                        status=normalized_status,
                        issue_date=self._parse_date(item.get("issue_date", "2025-01-01")),
                        due_date=self._parse_date(item.get("due_date", "2025-02-01"))
                    )
                    self.invoices[inv.invoice_id] = inv

        if os.path.exists(payments_path):
            with open(payments_path, "r") as f:
                pay_data = json.load(f)
                for item in pay_data:
                    # Map simplified payment methods, adjusting epic 1 to match Literal
                    method = item.get("payment_method", "credit_card")
                    
                    pay = Payment(
                        payment_id=item["payment_id"],
                        invoice_id=item["invoice_id"],
                        amount=Decimal(str(item["amount"])),
                        payment_method=method if method in ["credit_card", "ach", "wire", "check", "cash"] else "credit_card",
                        payment_date=item["payment_date"],
                        status=item.get("status", "completed")
                    )
                    self.payments[pay.payment_id] = pay

        if os.path.exists(ledger_path):
            with open(ledger_path, "r") as f:
                ledg_data = json.load(f)
                for item in ledg_data:
                    account_val = item["account"]
                    if account_val == "Accounts Receivable":
                        account_val = "accounts_receivable"
                        
                    le = LedgerEntry(
                        entry_id=item["entry_id"],
                        invoice_id=item["invoice_id"],
                        account=account_val if account_val in ["accounts_receivable", "revenue", "cash", "refunds"] else "accounts_receivable",
                        debit=Decimal(str(item["debit"])),
                        credit=Decimal(str(item["credit"])),
                        description=f"Seeded entry for {item['invoice_id']}",
                        posted_date=item["posted_date"]
                    )
                    self.ledger[le.entry_id] = le
    
    # --- CRUD Methods ---
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        return self.invoices.get(invoice_id)
        
    def list_invoices(self) -> List[Invoice]:
        return list(self.invoices.values())
        
    def save_invoice(self, invoice: Invoice):
        self.invoices[invoice.invoice_id] = invoice

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        return self.payments.get(payment_id)

    def list_payments(self) -> List[Payment]:
        return list(self.payments.values())

    def save_payment(self, payment: Payment):
        self.payments[payment.payment_id] = payment

    def list_ledger(self) -> List[LedgerEntry]:
        return list(self.ledger.values())

    def save_ledger_entry(self, entry: LedgerEntry):
        self.ledger[entry.entry_id] = entry
