# Epic 2 — CRM Layer: GoHighLevel API Simulation

> **Priority:** P0 (Foundation)  
> **Estimated Effort:** 3–4 days  
> **Dependencies:** Epic 1 (Data Simulation — for seeding the mock database)  
> **Owner:** Backend Engineer

---

## 1. Objective

Build a fully functional mock CRM API layer that simulates GoHighLevel-style endpoints. This layer serves as the **source-of-truth** for all sales-side data — contacts, deals, opportunities, and orders — and is the upstream data source that the Validation Engine reconciles against the Finance layer.

---

## 2. Business Context

GoHighLevel is a popular CRM for agencies and SMBs. In production, the integration would use GoHighLevel's REST API. For this portfolio project, we simulate the API to demonstrate:

- Realistic CRM data structures
- Order lifecycle management (create → approve → fulfill)
- Discount assignment workflows
- The CRM as the "expected" side of reconciliation

---

## 3. Functional Requirements

### 3.1 API Endpoints

All endpoints are REST JSON, prefixed with `/api/v1/crm/`.

#### Contacts

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/contacts` | List all contacts (paginated) |
| `GET` | `/contacts/{id}` | Get contact by ID |
| `POST` | `/contacts` | Create a new contact |
| `PUT` | `/contacts/{id}` | Update contact |
| `DELETE` | `/contacts/{id}` | Soft-delete contact |

#### Deals

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/deals` | List deals (filterable by stage, contact) |
| `GET` | `/deals/{id}` | Get deal by ID |
| `POST` | `/deals` | Create a new deal |
| `PUT` | `/deals/{id}` | Update deal stage/value |

#### Opportunities

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/opportunities` | List opportunities |
| `GET` | `/opportunities/{id}` | Get opportunity by ID |
| `POST` | `/opportunities` | Create opportunity tied to a deal |
| `PUT` | `/opportunities/{id}` | Update opportunity |

#### Orders

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/orders` | List all orders (filterable by status, date range) |
| `GET` | `/orders/{id}` | Get order by ID with full details |
| `POST` | `/orders` | Create a new order from opportunity |
| `PUT` | `/orders/{id}/status` | Update order status |
| `GET` | `/orders/{id}/discount` | Get discount details for an order |
| `POST` | `/orders/{id}/discount` | Apply discount to an order |
| `POST` | `/orders/{id}/approve` | Approve an order for invoicing |

### 3.2 Data Models

Use Pydantic models that align with Epic 1's generated entities:

```python
class Contact(BaseModel):
    contact_id: str
    name: str
    email: str
    company: str
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class Deal(BaseModel):
    deal_id: str
    contact_id: str
    stage: Literal["prospect", "negotiation", "proposal", "closed_won", "closed_lost"]
    value: Decimal
    assigned_to: str
    created_at: datetime
    updated_at: datetime

class Order(BaseModel):
    order_id: str
    opportunity_id: str
    contact_id: str
    line_items: list[LineItem]
    subtotal: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    approval_status: Literal["pending", "approved", "rejected"]
    order_status: Literal["draft", "confirmed", "fulfilled", "cancelled"]
    order_date: datetime
    approved_by: Optional[str]
    approved_at: Optional[datetime]
```

### 3.3 Business Rules (CRM-Side)

| Rule | Enforcement |
|---|---|
| Discount cap | Orders with `discount_pct > 15%` require explicit `approval_status = "approved"` |
| Order → Invoice gate | Only `approved` orders can trigger invoice generation |
| Deal stage progression | Deals must follow stage ordering (no backward transitions) |
| Contact required | Every Deal and Order must reference a valid `contact_id` |

### 3.4 Mock Data Store

- In-memory store (Python dict or SQLite) seeded from Epic 1's synthetic dataset on startup.
- Must support full CRUD operations during runtime.
- State resets on server restart (by re-loading seed data).

---

## 4. Technical Design

### 4.1 File Structure

```
backend/
  api/
    crm_simulator.py         # FastAPI router with all CRM endpoints
    crm_models.py             # Pydantic request/response models
    crm_store.py              # In-memory data store + CRUD operations
    crm_business_rules.py     # Discount cap, approval gate, etc.
    __init__.py
```

### 4.2 FastAPI Router Pattern

```python
from fastapi import APIRouter, HTTPException, Query

crm_router = APIRouter(prefix="/api/v1/crm", tags=["CRM Simulator"])

@crm_router.get("/orders", response_model=PaginatedResponse[OrderSummary])
async def list_orders(
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
): ...
```

### 4.3 Pagination & Filtering

All list endpoints must support:

- **Pagination:** `page` and `page_size` query params
- **Filtering:** Entity-specific filters (status, date range, contact_id)
- **Response format:**

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1000,
    "total_pages": 50
  }
}
```

### 4.4 Error Handling

| HTTP Code | Scenario |
|---|---|
| `400` | Invalid request body / failed Pydantic validation |
| `404` | Entity not found |
| `409` | Business rule violation (e.g., backward deal stage) |
| `422` | Unprocessable entity |

---

## 5. Acceptance Criteria

- [ ] All CRUD endpoints for Contacts, Deals, Opportunities, and Orders are implemented
- [ ] Endpoints return proper pagination and error responses
- [ ] Business rules are enforced (discount cap, approval gate, stage ordering)
- [ ] Mock store is seeded from Epic 1's synthetic data on startup
- [ ] All endpoints are documented in OpenAPI schema (auto-generated by FastAPI)
- [ ] Request/response models use Pydantic with validation
- [ ] Unit tests cover all endpoints and business rules

---

## 6. Testing Strategy

| Test | Description |
|---|---|
| `test_create_order` | POST a valid order, assert 201 and correct response body |
| `test_discount_cap_enforcement` | POST order with 20% discount and no approval → assert 409 |
| `test_pagination` | GET /orders with page_size=10, assert correct pagination metadata |
| `test_order_approval_flow` | Create order → approve → verify status change |
| `test_deal_stage_regression` | Attempt backward stage change → assert 409 |
| `test_contact_cascading` | Delete contact → verify related deals are handled |
| `test_filter_by_status` | GET /orders?status=confirmed → assert all returned orders are confirmed |

---

## 7. Integration Points

| Direction | Counterpart | Description |
|---|---|---|
| **← Inbound** | Epic 1 | Seeds the mock data store on startup |
| **→ Outbound** | Epic 4 | Validation Engine queries CRM for order data |
| **→ Outbound** | Epic 7 | OpenAPI Playground exposes CRM endpoints |

---

## 8. Out of Scope

- Real GoHighLevel API authentication / OAuth
- Webhooks or event-driven notifications
- Multi-tenant data isolation
- File uploads or media attachments
