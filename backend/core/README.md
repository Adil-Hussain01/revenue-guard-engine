# Backend Core Services

This directory contains the foundational, system-wide services for the Revenue Guard Engine. These modules provide the intelligence, compliance, and persistence infrastructure that powers the high-level API.

## Core Modules

### 1. Audit Logging System (Epic 5)
A structured, queryable trail of all system events. See [audit_models.py](file:///Users/adilhussain/Documents/AntiGravity/Revenue%20Leakage%20Detection%20&%20Validation%20Engine/backend/core/audit_models.py) and [audit_logger.py](file:///Users/adilhussain/Documents/AntiGravity/Revenue%20Leakage%20Detection%20&%20Validation%20Engine/backend/core/audit_logger.py).

### 2. Validation & Risk Scoring Engine (Epic 4)
The reconciliation intelligence that detects leakage and computes risk scores. 
**Detailed Documentation:** [VALIDATION_ENGINE.md](file:///Users/adilhussain/Documents/AntiGravity/Revenue%20Leakage%20Detection%20&%20Validation%20Engine/backend/core/VALIDATION_ENGINE.md)

---

## Architecture

This standalone Epic is comprised of 4 central files acting as the system interface:

1. `backend/core/audit_models.py`
   Contains the strict Pydantic definitions enforcing the schema of rules, validations, summary properties, and central `AuditLogEntry`.
   
2. `backend/core/audit_store.py`
   Provides file-based generic disk persistence in the format of JSON-Lines. 
   Files are saved incrementally per day into a local `logs/` directory.
   Upon startup, the store rebuilds an in-memory caching system based on transaction UUIDs and correlation IDs to guarantee high-performance, O(1) time complexity querying retrieval.

3. `backend/core/audit_logger.py`
   This is the business-level Service wrapper acting as an orchestrator. Downstream modules (Validation Engine, OpenAPI, CRM API) invoke standardized methods (e.g. `log_validation_start`, `log_risk_score`) to produce logs without worrying about structuring objects.
   
4. `backend/api/audit_controller.py`
   The REST interface implementation in FastAPI. Mounts to `/api/v1/audit/` and exposes API endpoints for paginated filtering, summary aggregation, payload extraction (JSON Blob download) and data purging hooks for retention rules compliance.

## Environment Initialization

The audit system requires no external dependencies (e.g., PostgreSQL, Redis), instead relying inherently on local volume persistence mapping.

Simply ensure you have standard dependencies installed:
```bash
pip install -r requirements.txt
```

## Running the API locally

You can view the interactive documentation for this particular route through Swagger simply by running:
```bash
uvicorn backend.main:app --reload
```
And navigating to: `http://localhost:8000/docs`

## Automated Testing

This module contains a comprehensive pytest suite mimicking enterprise acceptance criteria testing.
It validates correlation groupings, structural schema generation, timezone isolation, file persistence across simulator boots, and aggregated computational metrics.

To execute the test suite:
```bash
PYTHONPATH=. pytest tests/test_audit_logger.py -v
```
