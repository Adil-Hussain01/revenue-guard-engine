from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, date
from decimal import Decimal

# ---------------------------------------------------------
# Nested Models
# ---------------------------------------------------------
class InvoiceLineItem(BaseModel):
    product_id: str
    description: str
    quantity: int
    unit_price: Decimal
    amount: Decimal

# ---------------------------------------------------------
# Core Entities
# ---------------------------------------------------------
class Invoice(BaseModel):
    invoice_id: str
    order_id: str
    customer_id: str
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0.0")
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: Literal["draft", "sent", "partial", "paid", "overdue", "void"]
    issue_date: date
    due_date: date
    payment_terms: str = "Net 30"

class Payment(BaseModel):
    payment_id: str
    invoice_id: str
    amount: Decimal
    payment_method: Literal["credit_card", "ach", "wire", "check", "cash"]
    payment_date: datetime
    status: Literal["completed", "pending", "failed", "refunded"]
    reference_number: Optional[str] = None

class LedgerEntry(BaseModel):
    entry_id: str
    invoice_id: Optional[str] = None
    payment_id: Optional[str] = None
    account: Literal["accounts_receivable", "revenue", "cash", "refunds"]
    debit: Decimal
    credit: Decimal
    description: str
    posted_date: datetime

# ---------------------------------------------------------
# API Request/Response Schemas
# ---------------------------------------------------------
class InvoiceCreateRequest(BaseModel):
    order_id: str
    customer_id: str
    amount: Decimal
    issue_date: Optional[date] = None

class InvoiceUpdateRequest(BaseModel):
    status: Optional[Literal["draft", "sent", "partial", "paid", "overdue", "void"]] = None
    total_amount: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    
class PaymentCreateRequest(BaseModel):
    invoice_id: str
    amount: Decimal
    payment_method: Literal["credit_card", "ach", "wire", "check", "cash"]

# ---------------------------------------------------------
# Reporting Schemas
# ---------------------------------------------------------
class ReconciliationReport(BaseModel):
    total_crm_orders: int
    total_invoices: int
    matched: int
    mismatched_amount: int
    missing_invoice: int
    duplicate_invoice: int
    status_conflicts: int
    last_reconciled_at: datetime

class MismatchRecord(BaseModel):
    mismatch_type: Literal["ghost_invoice", "phantom_payment", "amount_drift", "status_conflict", "missing_invoice"]
    entity_id: str
    description: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
