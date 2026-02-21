# Developer Handover Document — Revenue Guard Engine

## 1. Project Overview
The Revenue Guard Engine is designed to detect "revenue leakage" — financial discrepancies between a CRM source of truth and an accounting system's ledger. This is a common problem in high-volume businesses where manual reconciliation is impossible.

### System Workflow
1. **Simulation:** `generate_data.py` creates a synthetic history of business events.
2. **Ingestion:** Data is loaded into mock CRM and Finance stores.
3. **Validation:** The `ValidationEngine` runs a suite of 12+ rules to identify anomalies.
4. **Scoring:** Detected anomalies are assigned risk scores based on monetary value and rule severity.
5. **Auditing:** Every detection event is logged to a structured JSON audit trail.
6. **Reporting:** Data is visualized via Matplotlib charts and accessible via an OpenAPI playground.

## 2. Functional Modules

| Module | Description | Location |
|---|---|---|
| **CRM Simulator** | Mimics GoHighLevel APIs for Contacts and Deals. | `backend/api/crm_simulator.py` |
| **Finance Simulator** | Mimics QuickBooks APIs for Invoices and Payments. | `backend/api/finance_simulator.py` |
| **Validation Engine** | Core logic for discrepancy detection. | `backend/core/validation_engine.py` |
| **Risk Scoring** | Logic for calculating transaction health scores. | `backend/core/risk_scoring.py` |
| **Audit Logger** | Persistent logging for validation hits. | `backend/core/audit_logger.py` |
| **Visualization** | Matplotlib-based chart generation. | `visualization/` |
| **Playground** | Unified FastAPI interface for all modules. | `playground/` |

## 3. Data Flow
The primary data flow is sequential:
1. **Synthetic Data** (JSON) -> Loaded into **Object Stores** (CRM/Finance).
2. **Validation Engine** queries both stores to find mismatches (e.g., Deal marked Won but no Invoice created).
3. **Anomalies** are passed to **Risk Engine** for scoring.
4. **Final Results** are emitted to **Audit Logs** and **Visualization**.

## 4. Configuration
Configuration handles data bounds and anomaly rates:
- **Location:** `backend/data/config.py`
- **Tuning:** Adjust `ANOMALY_RATES` to increase/decrease the frequency of specific leakage types.

## 5. Extension Guide

### Adding a New Validation Rule
1. Open `backend/core/validation_engine.py`.
2. Implement a new method that accepts CRM and Finance data.
3. Return a `ValidationResult` object.
4. Register the rule in the main execution loop.

### Adding a New Chart
1. Create a new plot function in `visualization/charts.py`.
2. Add it to the main `dashboard` generation script in `visualization/dashboard.py`.

### Adding API Endpoints
1. Create a new router in `backend/api/`.
2. Include the router in `playground/openapi_interface.py`.

## 6. Known Limitations
- **Simulation Only:** This project uses non-persistent, in-memory object stores. For production, these should be replaced with SQL/NoSQL databases.
- **Mock APIs:** External system integrations (GHL, QB) are simulated via API contracts, not actual OAuth connections.
- **Static Visualization:** Charts are generated as static images; an interactive JS-based frontend (e.g., React + D3) would be the next step.

## 7. Acceptance Criteria Checklist
- [x] Full data pipeline (Simulation -> Validation -> Visualization).
- [x] 12+ Validation Rules implemented.
- [x] Risk Scoring Model functional.
- [x] Interactive OpenAPI Playground.
- [x] Comprehensive test suite with 90%+ coverage on core logic.
