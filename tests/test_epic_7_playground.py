import pytest
from fastapi.testclient import TestClient
from playground.openapi_interface import app
from backend.api.crm_store import CRMStore
from backend.api.finance_store import FinanceStore
import os

client = TestClient(app)

def test_health_check():
    """GET /api/v1/system/health -> 200"""
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_system_info():
    """GET /api/v1/system/info -> 200"""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    assert "version" in response.json()
    assert response.json()["title"] == "Revenue Guard Engine — API Playground"

def test_playground_docs_load():
    """GET /playground -> 200 (Swagger UI)"""
    response = client.get("/playground")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

def test_redoc_loads():
    """GET /docs -> 200 (ReDoc)"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()

def test_system_reset():
    """POST /api/v1/system/reset -> 200"""
    # 1. Add some mock data to stores manually
    from backend.api.crm_simulator import get_store as get_crm_store
    from backend.api.finance_simulator import get_store as get_finance_store
    from backend.api.crm_models import Contact
    from datetime import datetime, timezone
    
    crm = get_crm_store()
    crm.add_contact(Contact(
        contact_id="TEMP-123", name="Temp", email="t@t.com", 
        company="T", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    ))
    
    # 2. Reset
    response = client.post("/api/v1/system/reset")
    assert response.status_code == 200
    
    # 3. Verify TEMP-123 is gone
    with pytest.raises(Exception): # CRMStore raises CRMException which might be wrapped or specific
        crm.get_contact("TEMP-123")

def test_root_redirect_info():
    """GET / -> 200 with playground URLs"""
    response = client.get("/")
    assert response.status_code == 200
    assert "playground_url" in response.json()
