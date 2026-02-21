# Epic 7 — OpenAPI Playground & API Interface

> **Priority:** P1  
> **Estimated Effort:** 2–3 days  
> **Dependencies:** Epic 2 (CRM), Epic 3 (Finance), Epic 4 (Validation), Epic 5 (Audit)  
> **Owner:** Backend Engineer

---

## 1. Objective

Build an interactive OpenAPI Playground (Swagger UI) that lets users test the entire system end-to-end — from creating CRM orders to running validations and inspecting audit logs — through a polished, self-documenting API interface.

---

## 2. Business Context

An interactive API playground is essential for portfolio demonstrations. It allows prospective clients to:

- Understand the system's capabilities without reading code
- Test the full workflow interactively
- See real-time results from the validation engine

---

## 3. Functional Requirements

### 3.1 Unified API Application

A single FastAPI application that mounts all routers:

| Router | Prefix | Source |
|---|---|---|
| CRM Simulator | `/api/v1/crm/` | Epic 2 |
| Finance Simulator | `/api/v1/finance/` | Epic 3 |
| Validation Engine | `/api/v1/validation/` | Epic 4 |
| Audit Logs | `/api/v1/audit/` | Epic 5 |
| System | `/api/v1/system/` | This epic |

### 3.2 System Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/system/health` | Health check |
| `GET` | `/api/v1/system/info` | System version, uptime, config |
| `POST` | `/api/v1/system/reset` | Reset all data stores to seed state |
| `POST` | `/api/v1/system/seed` | Re-generate and load synthetic data |

### 3.3 Interactive Workflow

The playground must support this end-to-end flow:

```
1. POST /crm/orders          → Create a CRM order
2. POST /finance/invoices     → Create an invoice for the order
3. POST /validation/validate/transaction/{order_id}  → Run validation
4. GET  /validation/results/{order_id}               → View risk score
5. GET  /audit/logs/transaction/{order_id}            → Inspect audit trail
```

### 3.4 Swagger UI Customization

- Custom title: "Revenue Guard Engine — API Playground"
- Organized tag groups: CRM, Finance, Validation, Audit, System
- Detailed descriptions for every endpoint
- Example request/response bodies for all POST endpoints
- Markdown descriptions with business context

### 3.5 OpenAPI Schema Enhancements

```python
app = FastAPI(
    title="Revenue Guard Engine",
    description="Revenue Leakage Detection & Validation Engine — Interactive API Playground",
    version="1.0.0",
    docs_url="/playground",
    redoc_url="/docs",
    openapi_tags=[
        {"name": "CRM Simulator", "description": "GoHighLevel-style CRM operations"},
        {"name": "Finance Simulator", "description": "QuickBooks-style accounting operations"},
        {"name": "Validation Engine", "description": "Risk scoring and reconciliation"},
        {"name": "Audit Logs", "description": "Audit trail inspection"},
        {"name": "System", "description": "Health, configuration, and data management"},
    ],
)
```

---

## 4. Technical Design

### 4.1 File Structure

```
playground/
  openapi_interface.py       # Main FastAPI app with all routers mounted
  app_config.py              # Application configuration
  startup.py                 # Data seeding and initialization
  __init__.py
```

### 4.2 Application Lifecycle

```python
@app.on_event("startup")
async def startup():
    """Seed data stores with synthetic dataset."""
    generator = SyntheticDataGenerator(config)
    dataset = generator.generate()
    crm_store.seed(dataset)
    finance_store.seed(dataset)
    audit_logger.log_event("system_startup")

@app.on_event("shutdown")
async def shutdown():
    audit_logger.log_event("system_shutdown")
```

### 4.3 CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 5. Acceptance Criteria

- [ ] Unified FastAPI app mounts all routers from Epics 2–5
- [ ] Swagger UI is accessible at `/playground` with custom branding
- [ ] ReDoc is accessible at `/docs`
- [ ] All endpoints have example request/response bodies
- [ ] End-to-end workflow (create order → validate → inspect) works
- [ ] System reset/seed endpoints correctly reinitialize data
- [ ] Health check returns meaningful status information
- [ ] CORS is configured for browser-based testing

---

## 6. Testing Strategy

| Test | Description |
|---|---|
| `test_health_check` | GET /system/health → assert 200 with status "ok" |
| `test_swagger_ui_loads` | GET /playground → assert 200 and HTML content |
| `test_end_to_end_flow` | Execute the 5-step workflow → assert each step succeeds |
| `test_system_reset` | Reset → assert stores return to seed state |
| `test_openapi_schema` | GET /openapi.json → assert valid schema with all endpoints |

---

## 7. Integration Points

- **← Inbound:** Mounts routers from Epics 2, 3, 4, 5
- **→ Outbound:** Provides unified entry point for all API consumers

## 8. Out of Scope

- Authentication / API key management
- Rate limiting
- WebSocket endpoints
- GraphQL interface
