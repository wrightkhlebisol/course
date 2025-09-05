import pytest
from fastapi.testclient import TestClient
import sys
sys.path.append('src')

from api.cost_api import app

client = TestClient(app)

def test_health_check():
    """Test API health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_tenants():
    """Test tenant listing endpoint"""
    response = client.get("/tenants")
    assert response.status_code == 200
    data = response.json()
    assert "tenants" in data
    assert isinstance(data["tenants"], list)

def test_get_configuration():
    """Test configuration endpoint"""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "pricing_models" in data
    assert "tenants" in data

def test_track_usage():
    """Test usage tracking endpoint"""
    usage_data = {
        "tenant_id": "engineering",
        "resource_type": "ingestion",
        "amount": 5.0,
        "unit": "GB",
        "metadata": {"source": "test"}
    }
    
    response = client.post("/usage/track", json=usage_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_calculate_costs():
    """Test cost calculation endpoint"""
    response = client.get("/costs/calculate?start_date=2025-06-01&end_date=2025-06-02")
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert "costs" in data

def test_dashboard_data():
    """Test dashboard data endpoint"""
    response = client.get("/dashboard/data")
    assert response.status_code == 200
    data = response.json()
    assert "tenants" in data
    assert "timestamp" in data
