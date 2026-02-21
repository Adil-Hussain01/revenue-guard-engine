# Validation & Risk Scoring Engine (Epic 4)

The **Validation & Risk Scoring Engine** is the core intelligence layer of the Revenue Guard system. It acts as an automated auditor that reconciles data between the **CRM (GHL Simulator)** and **Finance (QuickBooks Simulator)** systems to detect revenue leakage, pricing anomalies, and data drift.

## Core Architecture

The engine follows a pluggable, rule-based architecture located in `backend/core/`:

1.  **Rule Registry (`rule_registry.py`)**: A central store for all validation logic. Every check is implemented as a standalone class inheriting from `ValidationRule`.
2.  **Rule Evaluator (`rule_evaluator.py`)**: Orchestrates the execution of rules against a specific transaction context.
3.  **Risk Scoring Engine (`risk_scoring_engine.py`)**: Assigns weights to violations and computes a composite risk score (0-100).
4.  **Reconciliation Orchestrator (`reconciliation_engine.py`)**: The high-level service that fetches data from CRM/Finance stores and pipes it through the evaluator.

## Implemented Validation Rules

The engine currently executes **12 deterministic rules** categorized by their inspection area:

### Phase 1: Pricing Integrity
| Rule ID | Name | Severity | Weight | Description |
| :--- | :--- | :--- | :--- | :--- |
| **PRC-001** | Discount Threshold | Critical | 30 | Flags discounts >15% lacking explicit approval status. |
| **PRC-002** | Margin Protection | High | 20 | Detects items sold below the 10% minimum margin threshold. |
| **PRC-003** | Price Consistency | Critical | 30 | Checks for >1% drift between Order total and Invoice total. |
| **PRC-004** | Bulk Price Validation | Medium | 10 | Ensures bulk orders (>100 units) have a discount applied. |

### Phase 2: Order-Invoice Consistency
| Rule ID | Name | Severity | Weight | Description |
| :--- | :--- | :--- | :--- | :--- |
| **OIC-001** | Order-Invoice Mapping | Critical | 30 | Flags CRM orders that have no matching invoice in Finance. |
| **OIC-002** | Amount Matching | Critical | 30 | Strict $0.01 tolerance check between Order and Invoice totals. |
| **OIC-003** | Duplicate Invoice | High | 20 | Detects multiple invoices issued for a single CRM order. |
| **OIC-004** | Payment Completeness| High | 20 | Flags 'Paid' invoices where payment sum < total amount. |
| **OIC-005** | Stale Invoice | Medium | 10 | Identifies invoices unpaid for more than 60 days. |

### Phase 3: Cross-System Integrity
| Rule ID | Name | Severity | Weight | Description |
| :--- | :--- | :--- | :--- | :--- |
| **CSI-001** | Ghost Invoice | Critical | 30 | Detects Finance invoices referencing non-existent CRM orders. |
| **CSI-002** | Status Sync | High | 20 | Flags 'Fulfilled' CRM orders where the Invoice is 'Overdue'. |
| **CSI-003** | Ledger Balance | Critical | 30 | Ensures double-entry integrity (Debits == Credits) for the record. |

## Risk Scoring & Classification

The **Risk Score** is a weighted sum of all active violations, capped at a maximum of **100**. 

Transactions are classified into three buckets:
- **SAFE (0 - 30)**: Low risk, likely automated reconciliation.
- **MONITOR (31 - 70)**: High probability of leakage; requires partial review.
- **CRITICAL (71 - 100)**: confirmed anomaly; immediate audit required.

## API Integration

The engine is exposed via `/api/v1/validation/`:
- `POST /validate/transaction/{order_id}`: Trigger ad-hoc validation.
- `POST /run-full-scan`: Process every order in the system.
- `GET /statistics`: Aggregated system health metrics.
- `GET /risk-distribution`: Histogram data for visualization.

## Audit Trail

Every validation event is automatically streamed to the **Audit Logging System** (Epic 5), recording:
- Validation start/stop times.
- Specific rule results (Pass/Fail) with failure messages.
- Final Risk Score and classification.
- Correlation IDs for tracing the logic through the logs.
