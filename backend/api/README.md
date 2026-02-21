# External System Simulators (API Layer)

This directory contains the mock implementations of the external systems that the Revenue Guard Engine integrates with. These simulators allow for end-to-end testing without requiring live API keys or complex environment setups.

---

# CRM Mock Simulator (Epic 2)

The CRM Layer simulates the standard GoHighLevel REST API format serving as the absolute source-of-truth for sales interactions, customers, and pre-invoiced transaction data. 

## In-Memory Database Architecture

To isolate external dependencies and comply with the single self-contained application objective, this mock handles all data via `CRMStore` nested Python dictionaries representing the database.
- Memory stores are located and populated on application startup tracking `[Contacts, Deals, Opportunities, Orders]`.
- All `GET` list paths enable parameter search and simulated pagination identical to a true GHL setup.
- Generated synthetic data sets from Epic 1 (`generated_data/*.json`) seed the initial state automatically.

## Key Implemented Logic Rules

Business constraints simulated before allowing storage commits:

1. **Rule**: Orders created with a `>15%` auto-applied discount return a `409 Conflict` restricting save unless explicit internal managerial `approval_status == 'approved'` exists.
2. **Rule**: Deal tracking stages `(prospect -> negotiation -> proposal -> closed_*)` are strictly evaluated sequentially checking `idx`. Regression attempts throw `409` exceptions.
3. **Rule**: Entities must map appropriately via keys (`contact_id`, etc.).

# Finance Mock Simulator (Epic 3)

The Finance Layer simulates a QuickBooks Online REST API, providing the secondary data source for reconciliation. It manages the post-sale financial trail including invoices, payments, and ledger entries.

## Double-Entry Ledger Engine
Unlike simple data stores, the Finance Layer implements a deterministic **Double-Entry Ledger Engine** (`ledger_service.py`):
- Every transaction (Invoice creation, Payment received, Refund) triggers mirrored Debit/Credit entries.
- Accounts tracked: `accounts_receivable`, `revenue`, `cash`, `refunds`.
- Guarantees financial integrity: `sum(debits) == sum(credits)` for every order context.

## Business Rule Integration
- **Overpayment Protection**: Logic in `finance_business_rules.py` prevents recording payments that exceed the total invoice amount due.
- **Overdue Detection**: Automated status updates based on `due_date` comparisons.
- **Reconciliation API**: Provides a dedicated `/reconciliation/mismatches` endpoint for the dashboard.

## REST Overview
Mounted at `/api/v1/finance`:
- `GET /invoices`: View financial invoice sets.
- `POST /payments`: Record a new customer payment and trigger ledger updates.
- `GET /ledger/balance`: View current balances across the simulated company accounts.

---

## Development & Verification

Each simulator module contains an isolated testing suite:

```bash
# CRM Tests
PYTHONPATH=. pytest tests/test_crm_simulator.py -v

# Finance Tests
PYTHONPATH=. pytest tests/test_finance_simulator.py -v

# Validation Engine Tests
PYTHONPATH=. pytest tests/test_validation_engine.py -v
```
