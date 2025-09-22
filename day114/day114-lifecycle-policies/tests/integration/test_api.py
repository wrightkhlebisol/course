import pytest
import asyncio
from fastapi.testclient import TestClient
from src.backend.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_policies(client):
    """Test policy retrieval endpoint"""
    response = client.get("/api/policies")
    assert response.status_code == 200
    policies = response.json()
    assert isinstance(policies, list)

def test_get_tier_stats(client):
    """Test tier statistics endpoint"""
    response = client.get("/api/tier-stats")
    assert response.status_code == 200
    stats = response.json()
    assert isinstance(stats, dict)
    # Should have tier keys
    for tier in ["hot", "warm", "cold", "archive"]:
        if tier in stats:
            assert "file_count" in stats[tier]
            assert "size_gb" in stats[tier]
            assert "monthly_cost" in stats[tier]

def test_compliance_report(client):
    """Test compliance report generation"""
    response = client.get("/api/compliance-report?days=7")
    assert response.status_code == 200
    report = response.json()
    assert "total_policy_actions" in report
    assert "success_rate" in report
    assert "total_cost_savings" in report

def test_generate_logs(client):
    """Test log generation endpoint"""
    response = client.post("/api/generate-logs", params={"count": 10})
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "10" in result["message"]
