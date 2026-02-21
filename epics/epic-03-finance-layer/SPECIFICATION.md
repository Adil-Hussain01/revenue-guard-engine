# Epic 3 — Finance Layer: QuickBooks API Simulation

> **Priority:** P0 (Foundation)  
> **Estimated Effort:** 3–4 days  
> **Dependencies:** Epic 1 (Data Simulation — for seeding), Epic 2 (CRM Layer — for cross-referencing order IDs)  
> **Owner:** Backend Engineer

---

## 1. Objective

Build a mock QuickBooks-style accounting API layer that manages invoices, payments, and ledger entries. This layer acts as the **downstream financial system** that receives orders from the CRM and is the "actual" side that the Validation Engine compares against the "expected" CRM data.

---

## 2. Business Context

QuickBooks is the most widely used small-business accounting platform. In production, invoice creation and payment tracking would flow through QuickBooks' REST API. This simulation demonstrates:

- Invoice lifecycle management (draft → sent → paid / overdue)
- Payment reconciliation
- Ledger posting and balance tracking
- The finance system as the "actual" side of reconciliation

---

## 3. Functional Requirements

### 3.1 API Endpoints

All endpoints are REST JSON, prefixed with `/api/v1/finance/`.

#### Invoices

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/invoices` | List invoices (filterable by status, date, order_id) |
| `GET` | `/invoices/{id}` | Get invoice by ID |
| `POST` | `/invoices` | Create invoice from approved CRM order |
| `PUT` | `/invoices/{id}` | Update invoice details |
| `POST` | `/invoices/{id}/send` | Mark invoice as sent |
| `POST` | `/invoices/{id}/void` | Void an invoice |

#### Payments

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/payments` | List payments (filterable by invoice, date, method) |
| `GET` | `/payments/{id}` | Get payment details |
| `POST` | `/payments` | Record a payment against an invoice |
| `POST` | `/payments/{id}/refund` | Process a refund |

#### Ledger

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/ledger` | List ledger entries (filterable by account, date) |
| `GET` | `/ledger/balance` | Get current account balances |
| `GET` | `/ledger/reconciliation-report` | Get CRM ↔ Finance reconciliation summary |

#### Reconciliation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reconciliation/status` | Overall sync status between CRM and Finance |
| `GET` | `/reconciliation/mismatches` | List detected mismatches |

### 3.2 Data Models

```python
class Invoice(BaseModel):
    invoice_id: str
    order_id: str              # FK to CRM Order
    customer_id: str           # FK to CRM Contact
    line_items: list[InvoiceLineItem]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: Literal["draft", "sent", "partial", "paid", "overdue", "void"]
    issue_date: date
    due_date: date
    payment_terms: str         # e.g., "Net 30"

class Payment(BaseModel):
    payment_id: str
    invoice_id: str
    amount: Decimal
    payment_method: Literal["credit_card", "ach", "wire", "check", "cash"]
    payment_date: datetime
    status: Literal["completed", "pending", "failed", "refunded"]
    reference_number: Optional[str]

class LedgerEntry(BaseModel):
    entry_id: str
    invoice_id: Optional[str]
    payment_id: Optional[str]
    account: Literal["accounts_receivable", "revenue", "cash", "refunds"]
    debit: Decimal
    credit: Decimal
    description: str
    posted_date: datetime
```

### 3.3 Business Rules (Finance-Side)

| Rule | Enforcement |
|---|---|
| Invoice ↔ Order mapping | Every invoice must reference a valid `order_id` from CRM |
| Double-entry bookkeeping | Every transaction creates balanced debit + credit entries |
| Overdue detection | Invoices past `due_date` with `amount_due > 0` auto-transition to "overdue" |
| Payment cap | `sum(payments) ≤ invoice.total_amount` — no overpayment |
| Void cascading | Voiding an invoice reverses all ledger entries |

### 3.4 Status Drift Detection

The Finance layer must expose an internal method for detecting **status drift** — situations where CRM and Finance disagree:

| Drift Type | Description |
|---|---|
| Ghost Invoice | Invoice exists with no matching CRM order |
| Phantom Payment | Payment recorded for a void/cancelled invoice |
| Amount Drift | `invoice.total_amount ≠ order.total_amount` |
| Status Conflict | CRM order is "fulfilled" but invoice is "overdue" |

---

## 4. Technical Design

### 4.1 File Structure

```
backend/
  api/
    finance_simulator.py       # FastAPI router with all Finance endpoints
    finance_models.py          # Pydantic request/response models
    finance_store.py           # In-memory data store + CRUD
    finance_business_rules.py  # Double-entry, overdue detection, etc.
    ledger_service.py          # Ledger posting and balance calculation
    __init__.py
```

### 4.2 Double-Entry Ledger Implementation

Every financial event produces balanced ledger entries:

```python
# Invoice creation:
LedgerEntry(account="accounts_receivable", debit=amount, credit=0)
LedgerEntry(account="revenue", debit=0, credit=amount)

# Payment received:
LedgerEntry(account="cash", debit=amount, credit=0)
LedgerEntry(account="accounts_receivable", debit=0, credit=amount)
```

### 4.3 Reconciliation Report Structure

```json
{
  "total_crm_orders": 1000,
  "total_invoices": 962,
  "matched": 920,
  "mismatched_amount": 25,
  "missing_invoice": 38,
  "duplicate_invoice": 12,
  "status_conflicts": 17,
  "last_reconciled_at": "2026-02-21T15:00:00Z"
}
```

---

## 5. Acceptance Criteria

- [ ] All CRUD endpoints for Invoices, Payments, and Ledger are implemented
- [ ] Double-entry bookkeeping is enforced on all financial events
- [ ] Overdue detection runs automatically on invoice queries
- [ ] Payment cap prevents overpayment
- [ ] Reconciliation endpoints return accurate mismatch data
- [ ] Mock store is seeded from Epic 1's synthetic data on startup
- [ ] All endpoints are documented in OpenAPI schema
- [ ] Unit tests cover all endpoints, business rules, and edge cases

---

## 6. Testing Strategy

| Test | Description |
|---|---|
| `test_create_invoice` | POST invoice with valid order_id → assert 201 |
| `test_double_entry_balance` | After any transaction, assert total debits = total credits |
| `test_overpayment_rejection` | Pay more than amount_due → assert 409 |
| `test_overdue_transition` | Query invoice past due_date → assert status = "overdue" |
| `test_void_reversal` | Void invoice → assert ledger entries are reversed |
| `test_reconciliation_accuracy` | Seed known mismatches → assert reconciliation report matches |
| `test_status_drift_detection` | Inject status conflict → assert it appears in mismatches |

---

## 7. Integration Points

| Direction | Counterpart | Description |
|---|---|---|
| **← Inbound** | Epic 1 | Seeds the mock data store on startup |
| **← Inbound** | Epic 2 | References CRM order_id and contact_id |
| **→ Outbound** | Epic 4 | Validation Engine queries Finance for invoice/payment data |
| **→ Outbound** | Epic 7 | OpenAPI Playground exposes Finance endpoints |

---

## 8. Out of Scope

- Real QuickBooks OAuth or API integration
- Tax calculation engines
- Multi-currency support
- Bank feed reconciliation
