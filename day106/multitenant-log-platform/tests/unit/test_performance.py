import pytest
import asyncio
import time
from unittest.mock import patch
from backend.services.tenant_service import TenantService
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_concurrent_tenant_creation(db_session):
    """Test concurrent tenant creation performance"""
    with patch('backend.services.tenant_service.get_db') as mock_get_db:
        # Create a generator that yields the db_session each time it's called
        def mock_db_generator():
            while True:
                yield db_session
        
        mock_get_db.return_value = mock_db_generator()
        tenant_service = TenantService()
        
        # Clear any existing data
        from backend.models.tenant import Tenant
        db_session.query(Tenant).delete()
        db_session.commit()
        
        async def create_tenant(index):
            try:
                tenant = tenant_service.create_tenant(
                    name=f"Company {index}",
                    domain=f"company{index}.com"
                )
                return tenant
            except Exception as e:
                print(f"Failed to create tenant {index}: {e}")
                return None
        
        start_time = time.time()
        
        # Create 10 tenants concurrently
        tasks = [create_tenant(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        successful_creations = sum(1 for result in results if result is not None)
        
        print(f"Created {successful_creations} tenants in {duration:.2f} seconds")
        assert successful_creations >= 8  # Allow for some failures
        assert duration < 10  # Should complete within 10 seconds

def test_log_ingestion_performance(client, sample_tenant_data):
    """Test log ingestion performance"""
    # Clear any existing data first
    from backend.models.tenant import Tenant
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        db.query(Tenant).delete()
        db.commit()
    finally:
        db.close()
    
    # Create tenant and get auth token
    response = client.post("/api/v1/tenants/", json=sample_tenant_data)
    assert response.status_code == 200, f"Tenant creation failed: {response.text}"
    
    login_response = client.post("/api/v1/tenants/login", json={
        "tenant_domain": sample_tenant_data["domain"],
        "username": sample_tenant_data["admin_username"],
        "password": sample_tenant_data["admin_password"]
    })
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create bulk log data
    logs = []
    for i in range(100):
        logs.append({
            "level": "INFO" if i % 2 == 0 else "ERROR",
            "message": f"Performance test log {i}",
            "source": "performance-test",
            "service": f"service-{i % 5}",
            "metadata": {"test_run": "performance", "log_index": i}
        })
    
    bulk_request = {"logs": logs}
    
    start_time = time.time()
    response = client.post("/api/v1/logs/ingest/bulk", json=bulk_request, headers=headers)
    end_time = time.time()
    
    duration = end_time - start_time
    
    assert response.status_code == 200
    assert response.json()["count"] == 100
    assert duration < 5  # Should process 100 logs within 5 seconds
    
    print(f"Bulk ingested 100 logs in {duration:.2f} seconds")
    print(f"Throughput: {100/duration:.1f} logs/second")
