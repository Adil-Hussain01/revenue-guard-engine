import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from backend.main import app
from backend.api.crm_simulator import get_store
from backend.api.crm_store import CRMStore
from backend.api.crm_models import Contact, Deal, Opportunity, Order, LineItem
from decimal import Decimal

client = TestClient(app)

# --- Test Fixtures & Setup ---

@pytest.fixture
def clean_store():
    # Empty store for tests
    store = CRMStore(data_dir="invalid_dir_to_prevent_load")
    store.contacts.clear()
    store.deals.clear()
    store.opportunities.clear()
    store.orders.clear()
    return store

@pytest.fixture
def override_get_store(clean_store):
    app.dependency_overrides[get_store] = lambda: clean_store
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def setup_test_data(clean_store):
    # Setup base relational entities
    c = Contact(
        contact_id="CNT-TEST", name="Test User", email="test@test.com", 
        company="Test Co", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    clean_store.add_contact(c)
    
    d = Deal(
        deal_id="DEL-TEST", contact_id="CNT-TEST", stage="proposal",
        value=Decimal("1000.00"), assigned_to="user1", 
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    clean_store.add_deal(d)
    
    o = Opportunity(
        opportunity_id="OPP-TEST", deal_id="DEL-TEST", contact_id="CNT-TEST",
        status="open", expected_close_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    clean_store.add_opportunity(o)
    
    return clean_store

# --- Tests based on Acceptance Criteria ---

def test_create_order(override_get_store, setup_test_data):
    """POST a valid order, assert 201 and correct response body"""
    payload = {
        "opportunity_id": "OPP-TEST",
        "contact_id": "CNT-TEST",
        "line_items": [
            {
                "product_id": "P1",
                "product_name": "Test Product",
                "quantity": 2,
                "unit_price": "500.00",
                "total_price": "1000.00"
            }
        ],
        "discount_pct": "10.0"
    }
    
    res = client.post("/api/v1/crm/orders", json=payload)
    assert res.status_code == 201
    
    data = res.json()
    assert data["order_id"].startswith("ORD-")
    assert float(data["subtotal"]) == 1000.0
    assert float(data["discount_pct"]) == 10.0
    # 10% of 1000 = 100
    assert float(data["discount_amount"]) == 100.0 
    assert float(data["total_amount"]) == 900.0
    assert data["approval_status"] == "pending"
    assert data["order_status"] == "draft"

def test_discount_cap_enforcement(override_get_store, setup_test_data):
    """POST order with 20% discount and no approval -> assert 409"""
    payload = {
        "opportunity_id": "OPP-TEST",
        "contact_id": "CNT-TEST",
        "line_items": [
            {"product_id": "P1", "product_name": "Test", "quantity": 1, "unit_price": "100.0", "total_price": "100.0"}
        ],
        "discount_pct": "20.0"
    }
    
    # Creation blocks immediately
    res = client.post("/api/v1/crm/orders", json=payload)
    assert res.status_code == 409
    assert "discount" in res.json()["detail"].lower()

def test_order_approval_flow(override_get_store, setup_test_data):
    """Create order -> approve -> verify status change"""
    # 1. Create a safe order
    payload = {
        "opportunity_id": "OPP-TEST",
        "contact_id": "CNT-TEST",
        "line_items": [{"product_id": "P1", "product_name": "Test", "quantity": 1, "unit_price": "100.0", "total_price": "100.0"}],
        "discount_pct": "0.0"
    }
    res_create = client.post("/api/v1/crm/orders", json=payload)
    order_id = res_create.json()["order_id"]
    
    # 2. Try to move to confirmed before approval -> Expect 409 Due to Invoice Gate
    res_fail = client.put(f"/api/v1/crm/orders/{order_id}/status", json={"order_status": "confirmed"})
    assert res_fail.status_code == 409
    
    # 3. Approve it
    res_app = client.post(f"/api/v1/crm/orders/{order_id}/approve")
    assert res_app.status_code == 200
    assert res_app.json()["approval_status"] == "approved"
    
    # 4. Move to confirmed
    res_succ = client.put(f"/api/v1/crm/orders/{order_id}/status", json={"order_status": "confirmed"})
    assert res_succ.status_code == 200
    assert res_succ.json()["order_status"] == "confirmed"

def test_deal_stage_regression(override_get_store, setup_test_data):
    """Attempt backward stage change -> assert 409"""
    # Setup deal is at "proposal"
    res = client.put("/api/v1/crm/deals/DEL-TEST", json={"stage": "prospect"})
    assert res.status_code == 409
    assert "Cannot move deal backward" in res.json()["detail"]

def test_contact_cascading(override_get_store, setup_test_data):
    """Delete contact -> verify related logic"""
    # Using our soft-delete spec
    res = client.delete("/api/v1/crm/contacts/CNT-TEST")
    assert res.status_code == 204
    
    # Should still exist but be inactive
    res_get = client.get("/api/v1/crm/contacts/CNT-TEST")
    assert res_get.status_code == 200
    assert res_get.json()["is_active"] is False

def test_filter_by_status_and_pagination(override_get_store, setup_test_data):
    """GET /orders?status=confirmed -> assert all returned orders are confirmed"""
    store = setup_test_data
    # Inject 5 draft, 5 confirmed
    for i in range(10):
        status = "draft" if i < 5 else "confirmed"
        order = Order(
            order_id=f"ORD-MULTI-{i}",
            opportunity_id="OPP-TEST",
            contact_id="CNT-TEST",
            line_items=[],
            subtotal=Decimal("100"),
            discount_pct=Decimal("0"),
            discount_amount=Decimal("0"),
            total_amount=Decimal("100"),
            approval_status="pending",
            order_status=status,
            order_date=datetime.now(timezone.utc)
        )
        store.add_order(order)
        
    res = client.get("/api/v1/crm/orders?status=confirmed&page=1&page_size=3")
    assert res.status_code == 200
    data = res.json()
    assert len(data["data"]) == 3
    assert data["pagination"]["total_items"] == 5
    assert data["pagination"]["total_pages"] == 2
    assert all(o["order_status"] == "confirmed" for o in data["data"])
