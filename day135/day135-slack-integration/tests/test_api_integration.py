import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestAPIIntegration:
    def test_health_check(self, client):
        """Test health check endpoint"""
        with patch('src.backend.main.redis_client') as mock_redis:
            mock_redis.ping.return_value = True
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data

    def test_get_stats(self, client):
        """Test statistics endpoint"""
        with patch('src.backend.main.redis_client') as mock_redis:
            mock_redis.get.return_value = "5"
            mock_redis.keys.return_value = ["key1", "key2", "key3"]
            mock_redis.llen.return_value = 2
            
            response = client.get("/api/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "current_rate_per_minute" in data
            assert "recent_notifications" in data
            assert "queued_alerts" in data

    def test_send_alert(self, client):
        """Test alert sending endpoint"""
        alert_data = {
            "id": "test-123",
            "title": "Test Alert",
            "message": "Test message",
            "severity": "error",
            "service": "test-service",
            "component": "test-component",
            "timestamp": "2025-05-20T10:00:00Z",
            "metadata": {}
        }
        
        response = client.post("/api/alerts/send", json=alert_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["alert_id"] == "test-123"

    def test_generate_test_alert(self, client):
        """Test test alert generation"""
        with patch('src.backend.main.slack_service') as mock_service:
            mock_service.send_alert = AsyncMock(return_value=type('obj', (object,), {
                'dict': lambda: {"status": "sent", "channel": "#test"}
            })())
            
            response = client.post("/api/alerts/test?severity=warning")
            
            assert response.status_code == 200
            data = response.json()
            assert "alert" in data
            assert "status" in data
            assert data["alert"]["severity"] == "warning"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
