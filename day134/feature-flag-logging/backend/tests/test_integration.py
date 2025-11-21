import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_flag_api():
    """Test creating flag through API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/flags", json={
            "name": "api_test_flag",
            "description": "API test flag",
            "enabled": True,
            "rollout_percentage": "50"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "api_test_flag"
        assert data["enabled"] == True

@pytest.mark.asyncio
async def test_get_flags_api():
    """Test getting all flags through API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/flags")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_evaluate_flag_api():
    """Test flag evaluation through API"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create flag first
        create_response = await ac.post("/api/v1/flags", json={
            "name": "eval_api_test",
            "enabled": True,
            "rollout_percentage": "100"
        })
        assert create_response.status_code == 200
        
        # Evaluate flag
        eval_response = await ac.post("/api/v1/flags/evaluate", json={
            "flag_name": "eval_api_test",
            "user_context": {"user_id": "test_user"},
            "default_value": False
        })
        
        assert eval_response.status_code == 200
        data = eval_response.json()
        assert data["enabled"] == True

if __name__ == "__main__":
    pytest.main([__file__])
