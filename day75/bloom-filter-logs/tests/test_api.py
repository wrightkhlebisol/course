import pytest
import httpx
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
API_BASE_URL = "http://localhost:8001"

@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "filters_active" in data
        except httpx.ConnectError:
            pytest.skip("API server not running")

@pytest.mark.asyncio
async def test_add_log_entry():
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "log_type": "error_logs",
                "log_key": "test_error_123",
                "metadata": {"severity": "high"}
            }
            response = await client.post(f"{API_BASE_URL}/logs/add", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "added"
            assert data["log_type"] == "error_logs"
            assert data["log_key"] == "test_error_123"
            assert "processing_time_ms" in data
        except httpx.ConnectError:
            pytest.skip("API server not running")

@pytest.mark.asyncio
async def test_query_log_entry():
    async with httpx.AsyncClient() as client:
        try:
            # First add an entry
            add_payload = {
                "log_type": "error_logs",
                "log_key": "query_test_error_456"
            }
            await client.post(f"{API_BASE_URL}/logs/add", json=add_payload)
            
            # Then query it
            query_payload = {
                "log_type": "error_logs",
                "log_key": "query_test_error_456"
            }
            response = await client.post(f"{API_BASE_URL}/logs/query", json=query_payload)
            assert response.status_code == 200
            data = response.json()
            assert data["might_exist"] == True
            assert data["confidence"] == "probably_exists"
            assert "processing_time_ms" in data
        except httpx.ConnectError:
            pytest.skip("API server not running")

@pytest.mark.asyncio
async def test_query_non_existent():
    async with httpx.AsyncClient() as client:
        try:
            query_payload = {
                "log_type": "error_logs", 
                "log_key": "definitely_non_existent_key_999999"
            }
            response = await client.post(f"{API_BASE_URL}/logs/query", json=query_payload)
            assert response.status_code == 200
            data = response.json()
            # This should return False (definitely not exist)
            assert data["might_exist"] == False
            assert data["confidence"] == "definitely_not_exist"
        except httpx.ConnectError:
            pytest.skip("API server not running")

@pytest.mark.asyncio 
async def test_statistics_endpoint():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/stats")
            assert response.status_code == 200
            data = response.json()
            
            # Should have our filter types
            assert "error_logs" in data
            assert "access_logs" in data
            assert "security_logs" in data
            
            # Each filter should have expected stats
            for filter_name, stats in data.items():
                assert "elements_added" in stats
                assert "queries_made" in stats
                assert "memory_usage_bytes" in stats
                assert "false_positive_rate" in stats
        except httpx.ConnectError:
            pytest.skip("API server not running")

if __name__ == "__main__":
    # Run specific tests
    asyncio.run(test_health_endpoint())
    print("✅ Health endpoint test passed")
    
    asyncio.run(test_add_log_entry())
    print("✅ Add log entry test passed")
    
    asyncio.run(test_query_log_entry())
    print("✅ Query log entry test passed")
    
    asyncio.run(test_statistics_endpoint())
    print("✅ Statistics endpoint test passed")
    
    print("🎉 All API tests completed successfully!")
