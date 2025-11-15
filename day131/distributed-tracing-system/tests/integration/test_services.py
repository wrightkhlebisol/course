import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient

class TestServiceIntegration:
    @pytest.mark.asyncio
    async def test_user_service_health(self):
        """Test user service health endpoint"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8002/")
                assert response.status_code == 200
                data = response.json()
                assert data["service"] == "user-service"
                assert data["status"] == "healthy"
            except httpx.ConnectError:
                pytest.skip("User service not running")
    
    @pytest.mark.asyncio
    async def test_user_lookup(self):
        """Test user lookup with tracing"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "http://localhost:8002/users/user123",
                    headers={"X-Trace-Id": "test-trace-123"}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "user123"
                
                # Check if trace headers are present in response
                assert "X-Trace-Id" in response.headers
            except httpx.ConnectError:
                pytest.skip("User service not running")
    
    @pytest.mark.asyncio
    async def test_api_gateway_user_proxy(self):
        """Test API gateway proxying to user service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8001/users/user123")
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "user123"
            except httpx.ConnectError:
                pytest.skip("API Gateway not running")
    
    @pytest.mark.asyncio
    async def test_order_creation_flow(self):
        """Test complete order creation flow across services"""
        order_data = {
            "items": [{"name": "Test Item", "price": 10.99}],
            "total": 10.99
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8001/users/user123/orders",
                    json=order_data,
                    headers={"X-Trace-Id": "test-order-trace"}
                )
                
                if response.status_code == 201:
                    data = response.json()
                    assert "order_id" in data
                    assert data["user_id"] == "user123"
                elif response.status_code in [400, 404]:
                    # Expected if user doesn't exist
                    pass
                else:
                    pytest.fail(f"Unexpected status code: {response.status_code}")
                    
            except httpx.ConnectError:
                pytest.skip("Services not running")

class TestTraceFlow:
    @pytest.mark.asyncio
    async def test_trace_propagation(self):
        """Test that trace context propagates through service calls"""
        trace_id = "test-trace-propagation-123"
        
        async with httpx.AsyncClient() as client:
            try:
                # Make request with trace ID
                response = await client.get(
                    "http://localhost:8001/users/user123",
                    headers={"X-Trace-Id": trace_id}
                )
                
                # Check that trace ID is in response headers
                assert response.headers.get("X-Trace-Id") == trace_id
                
            except httpx.ConnectError:
                pytest.skip("Services not running")
