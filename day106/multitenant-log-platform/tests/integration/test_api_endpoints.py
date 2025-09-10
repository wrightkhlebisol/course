import pytest
from fastapi.testclient import TestClient

def test_create_tenant_endpoint(client, sample_tenant_data):
    """Test tenant creation endpoint"""
    response = client.post("/api/v1/tenants/", json=sample_tenant_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_tenant_data["name"]
    assert data["domain"] == sample_tenant_data["domain"]
    assert data["status"] == "active"

def test_login_endpoint(client, sample_tenant_data):
    """Test login endpoint"""
    # Create tenant first
    client.post("/api/v1/tenants/", json=sample_tenant_data)
    
    # Test login
    login_data = {
        "tenant_domain": sample_tenant_data["domain"],
        "username": sample_tenant_data["admin_username"],
        "password": sample_tenant_data["admin_password"]
    }
    
    response = client.post("/api/v1/tenants/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "tenant_id" in data
    assert data["username"] == sample_tenant_data["admin_username"]

def test_log_ingestion_endpoint(client, sample_tenant_data):
    """Test log ingestion endpoint"""
    # Create tenant and get auth token
    client.post("/api/v1/tenants/", json=sample_tenant_data)
    
    login_response = client.post("/api/v1/tenants/login", json={
        "tenant_domain": sample_tenant_data["domain"],
        "username": sample_tenant_data["admin_username"],
        "password": sample_tenant_data["admin_password"]
    })
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test log ingestion
    log_data = {
        "level": "INFO",
        "message": "Test log message",
        "source": "test-app",
        "service": "auth-service",
        "metadata": {"user_id": "123"}
    }
    
    response = client.post("/api/v1/logs/ingest", json=log_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"

def test_tenant_isolation(client):
    """Test that tenants cannot access each other's data"""
    # Clear any existing data first
    from backend.models.tenant import Tenant
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        db.query(Tenant).delete()
        db.commit()
    finally:
        db.close()
    
    # Create two tenants
    tenant1_data = {
        "name": "Company 1",
        "domain": "company1.com",
        "service_tier": "basic",
        "admin_email": "admin1@company1.com",
        "admin_username": "admin1",
        "admin_password": "password123"
    }
    
    tenant2_data = {
        "name": "Company 2", 
        "domain": "company2.com",
        "service_tier": "basic",
        "admin_email": "admin2@company2.com",
        "admin_username": "admin2",
        "admin_password": "password123"
    }
    
    response1 = client.post("/api/v1/tenants/", json=tenant1_data)
    response2 = client.post("/api/v1/tenants/", json=tenant2_data)
    
    assert response1.status_code == 200, f"Tenant 1 creation failed: {response1.text}"
    assert response2.status_code == 200, f"Tenant 2 creation failed: {response2.text}"
    
    # Get tokens for both tenants
    token1_response = client.post("/api/v1/tenants/login", json={
        "tenant_domain": "company1.com",
        "username": "admin1",
        "password": "password123"
    })
    
    token2_response = client.post("/api/v1/tenants/login", json={
        "tenant_domain": "company2.com", 
        "username": "admin2",
        "password": "password123"
    })
    
    assert token1_response.status_code == 200, f"Login 1 failed: {token1_response.text}"
    assert token2_response.status_code == 200, f"Login 2 failed: {token2_response.text}"
    
    token1 = token1_response.json()["access_token"]
    token2 = token2_response.json()["access_token"]
    
    # Ingest logs for tenant 1
    log_data = {
        "level": "INFO",
        "message": "Tenant 1 log message",
        "service": "tenant1-service"
    }
    
    client.post("/api/v1/logs/ingest", json=log_data, 
                headers={"Authorization": f"Bearer {token1}"})
    
    # Search logs with tenant 2 token - should not see tenant 1 logs
    search_response = client.post("/api/v1/logs/search", 
                                 json={"limit": 100},
                                 headers={"Authorization": f"Bearer {token2}"})
    
    assert search_response.status_code == 200
    logs = search_response.json()["logs"]
    
    # Tenant 2 should not see any logs (since they didn't create any)
    assert len(logs) == 0
