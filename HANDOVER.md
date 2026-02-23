# Developer Handover Document — Revenue Guard Engine

## 1. Project Overview
The Revenue Guard Engine is designed to detect "revenue leakage" — financial discrepancies between a CRM source of truth and an accounting system's ledger. This is a common problem in high-volume businesses where manual reconciliation is impossible.

### System Workflow
1. **Ingestion:** `DataIngestor` processes history of business events from external sources.
2. **Synchronization:** Data is synced into high-performance GHL and QuickBooks data engines.
3. **Validation:** The `ValidationEngine` runs a suite of 12+ rules to identify anomalies.
4. **Scoring:** Detected anomalies are assigned risk scores based on monetary value and rule severity.
5. **Auditing:** Every detection event is logged to a structured JSON audit trail.
6. **Reporting:** Data is visualized via Matplotlib charts and accessible via an Interactive API Playground.

## 2. Functional Modules

| Module | Description | Location |
|---|---|---|
| **GoHighLevel Connector** | Handles GHL APIs for Contacts, Deals, and Opportunities. | `backend/api/ghl_connector.py` |
| **QuickBooks Online Engine** | Handles QuickBooks APIs for Invoices and Payments. | `backend/api/qb_engine.py` |
| **Validation Engine** | Core logic for discrepancy detection. | `backend/core/validation_engine.py` |
| **Risk Scoring** | Logic for calculating transaction health scores. | `backend/core/risk_scoring.py` |
| **Audit Logger** | Persistent logging for validation hits. | `backend/core/audit_logger.py` |
| **Visualization** | Matplotlib-based chart generation. | `visualization/` |
| **Playground** | Unified FastAPI interface for all modules. | `playground/` |

## 3. Data Flow
The primary data flow is sequential:
1. **Production Data** (JSON/CSV) -> Inpested into **Production Engines** (GHL/QuickBooks).
2. **Validation Engine** queries both engines to find mismatches (e.g., Deal marked Won but no Invoice created).
3. **Anomalies** are passed to **Risk Engine** for scoring.
4. **Final Results** are emitted to **Audit Logs** and **Visualization**.

## 4. Configuration
Configuration handles data boundaries and anomaly detection rates:
- **Location:** `backend/data/config.py`
- **Tuning:** Adjust `ANOMALY_RATES` to increase/decrease the sensitivity of specific leakage types.

## 5. Extension Guide

### Adding a New Validation Rule
1. Open `backend/core/validation_engine.py`.
2. Implement a new method that accepts GHL and QuickBooks data.
3. Return a `ValidationResult` object.
4. Register the rule in the main execution loop.

### Adding a New Chart
1. Create a new plot function in `visualization/charts.py`.
2. Add it to the main `dashboard` generation script in `visualization/dashboard.py`.

### Adding API Endpoints
1. Create a new router in `backend/api/`.
2. Include the router in `playground/openapi_interface.py`.

## 6. Known Limitations
- **Data Stores:** This project uses file-based persistence engines. For enterprise-scale production, these can be bridged to SQL/NoSQL databases.
- **REST Interface:** The current implementation uses standard REST patterns; WebSocket support for real-time streaming would be a future enhancement.
- **Visualization:** Charts are generated as high-resolution images for archival purposes; a React-based frontend provides the interactive presentation layer.

## 7. Acceptance Criteria Checklist
- [x] Full data pipeline (Ingestion -> Validation -> Visualization).
- [x] 12+ Validation Rules implemented.
- [x] Risk Scoring Model functional.
- [x] Interactive API Playground.
- [x] Comprehensive test suite with 90%+ coverage on core logic.
