from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Contact(BaseModel):
    """
    Simulates a GoHighLevel CRM Contact.
    """
    contact_id: str
    name: str
    email: str
    company: str
    created_at: datetime

class Deal(BaseModel):
    """
    Simulates a GoHighLevel CRM Deal representing a potential sale.
    """
    deal_id: str
    contact_id: str
    stage: str
    value: float
    assigned_to: str
    created_at: datetime

class Opportunity(BaseModel):
    """
    Simulates a GoHighLevel Opportunity line item attached to a Deal.
    Includes potential discount proposals.
    """
    opportunity_id: str
    deal_id: str
    product_id: str
    quantity: int
    unit_price: float
    discount_pct: float
    approval_status: str

class Order(BaseModel):
    """
    Simulates a finalized GoHighLevel CRM Order.
    This acts as the source of truth for total expected value.
    """
    order_id: str
    opportunity_id: str
    contact_id: str
    total_amount: float
    discount_applied: float
    order_date: datetime
    status: str

class Invoice(BaseModel):
    """
    Simulates a QuickBooks Accounting Invoice mapping to a CRM Order.
    Subject to anomalies like missing records or pricing drifts.
    """
    invoice_id: str
    order_id: str
    amount_due: float
    amount_paid: float
    status: str
    issue_date: datetime
    due_date: datetime

class Payment(BaseModel):
    """
    Simulates a QuickBooks Payment mapped to a specific Invoice.
    """
    payment_id: str
    invoice_id: str
    amount: float
    payment_method: str
    payment_date: datetime
    status: str

class LedgerEntry(BaseModel):
    """
    Simulates a QuickBooks double-entry Ledger record matching a Payment.
    """
    entry_id: str
    invoice_id: str
    debit: float
    credit: float
    account: str
    posted_date: datetime

class AnomalyRecord(BaseModel):
    """
    Ground truth record defining exactly what business noise was proactively injected
    during dataset generation. Used by validation engines to calculate recall/accuracy.
    """
    anomaly_id: str
    type: str # e.g. "pricing_drift"
    affected_entity: str
    entity_id: str
    related_entity_id: Optional[str] = None
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    drift_pct: Optional[float] = None
    injected_at: datetime

class GeneratedDataset(BaseModel):
    """
    Container aggregation holding the entire simulated cross-platform dataset.
    """
    contacts: List[Contact]
    deals: List[Deal]
    opportunities: List[Opportunity]
    orders: List[Order]
    invoices: List[Invoice]
    payments: List[Payment]
    ledger_entries: List[LedgerEntry]
    anomaly_manifest: List[AnomalyRecord]
