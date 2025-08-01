"""
Tests for FastAPI recommendation service
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.recommendation_service import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_stats():
    """Test stats endpoint"""
    response = client.get("/api/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_incidents" in data
    assert "total_solutions" in data
    assert "model_status" in data

def test_get_recommendations():
    """Test recommendations endpoint"""
    incident_data = {
        "title": "Test Database Error",
        "description": "Database connection timeout in production",
        "error_type": "database_connectivity",
        "affected_service": "test-service",
        "severity": "high",
        "environment": "production",
        "logs": ["ERROR: connection timeout", "Failed to connect"],
        "metrics": {"response_time": 30000}
    }
    
    response = client.post("/api/recommendations", json=incident_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "recommendations" in data
    assert "processing_time_ms" in data
    assert "similar_incidents_count" in data
    assert isinstance(data["recommendations"], list)

def test_submit_feedback():
    """Test feedback submission"""
    feedback_data = {
        "incident_id": "inc_001",
        "solution_id": "sol_001", 
        "was_helpful": True,
        "resolution_time": 15,
        "comments": "This solution worked great!"
    }
    
    response = client.post("/api/feedback", json=feedback_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "feedback_recorded"

def test_invalid_incident_data():
    """Test handling of invalid incident data"""
    invalid_data = {
        "title": "",  # Empty title
        "description": "Test description"
        # Missing required fields
    }
    
    response = client.post("/api/recommendations", json=invalid_data)
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
