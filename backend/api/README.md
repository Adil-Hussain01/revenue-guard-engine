# Production Integration Layers (API Engine)

This directory contains the core integration logic for the external systems (GoHighLevel and QuickBooks Online) that the Revenue Guard Engine synchronizes with. These connectors handle complex relational mapping and business logic validation.

---

# GoHighLevel Connector (Epic 2)

The GHL Connector handles the absolute source-of-truth for sales interactions, customers, and pre-invoiced transaction data.

## Persistent Object Engine

This engine processes data via `CRMStore`, tracking `[Contacts, Deals, Opportunities, Orders]`.
- Memory-mapped stores are populated on system initialization.
- All `GET` paths enable high-performance filtering and pagination identical to production environments.

## Production Logic Rules

Business constraints applied during the integration lifecycle:

1. **Rule**: Orders with unauthorized discounts return a `409 Conflict` to prevent financial leakage at the source.
2. **Rule**: Deal stage progression is strictly enforced to maintain sales pipeline integrity.

# QuickBooks Online Engine (Epic 3)

The QuickBooks Engine provides the deep financial reconciliation layer, managing the end-to-end invoice lifecycle.

## Double-Entry Ledger System
The engine implements a deterministic **Double-Entry Ledger** (`ledger_service.py`):
- Every financial event (Invoice, Payment, Refund) triggers mirrored Debit/Credit entries.
- Accounts tracked: `accounts_receivable`, `revenue`, `cash`, `refunds`.
- Guarantees financial auditability: `sum(debits) == sum(credits)`.

## Validation Strategy
- **Overpayment Protection**: Prevents recording payments that exceed the total invoice liability.
- **Aging & Overdue Tracking**: Automated status reconciliation based on dynamic due dates.
- **Reconciliation Interface**: Provides a dedicated `/reconciliation/mismatches` endpoint.

---

## Technical Verification

To execute the test suite for these engines:

```bash
# GHL Connector Tests
PYTHONPATH=. pytest tests/test_ghl_connector.py -v

# QuickBooks Engine Tests
PYTHONPATH=. pytest tests/test_qb_engine.py -v
```
