import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.provisioning import ProvisioningService
from services.security import SecurityService
from services.monitoring import MonitoringService
from workflows.tenant_orchestrator import TenantOrchestrator

@pytest.fixture
def provisioning_service():
    return ProvisioningService()

@pytest.fixture
def security_service():
    return SecurityService()

@pytest.fixture
def monitoring_service():
    return MonitoringService()

@pytest.fixture
def orchestrator(provisioning_service, security_service, monitoring_service):
    return TenantOrchestrator(provisioning_service, security_service, monitoring_service)

class TestProvisioningService:
    @pytest.mark.asyncio
    async def test_provision_tenant_resources(self, provisioning_service):
        tenant_id = "test-tenant-123"
        plan = "basic"
        config = {"custom_setting": "value"}
        
        result = await provisioning_service.provision_tenant_resources(tenant_id, plan, config)
        
        assert result["status"] == "provisioned"
        assert "resources" in result
        assert result["resources"]["log_retention_days"] == 30
        assert result["resources"]["max_ingestion_rate"] == 1000

    @pytest.mark.asyncio 
    async def test_deprovision_tenant_resources(self, provisioning_service):
        tenant_id = "test-tenant-123"
        
        # First provision to have something to deprovision
        await provisioning_service.provision_tenant_resources(tenant_id, "basic", {})
        
        result = await provisioning_service.deprovision_tenant_resources(tenant_id)
        
        assert result["status"] == "deprovisioned"
        assert result["archived"] == True

class TestSecurityService:
    @pytest.mark.asyncio
    async def test_setup_tenant_security(self, security_service):
        tenant_id = "test-tenant-123"
        tenant_data = {"plan": "pro"}
        
        result = await security_service.setup_tenant_security(tenant_id, tenant_data)
        
        assert "api_key" in result
        assert result["api_key"].startswith("tnt_")
        assert "access_policies" in result
        assert result["access_policies"]["config_write"] == True  # Pro plan feature

    @pytest.mark.asyncio
    async def test_revoke_tenant_security(self, security_service):
        tenant_id = "test-tenant-123"
        
        # First setup security
        await security_service.setup_tenant_security(tenant_id, {"plan": "basic"})
        
        result = await security_service.revoke_tenant_security(tenant_id)
        
        assert "revoked_keys" in result
        assert result["revoked_keys"] >= 1

class TestMonitoringService:
    @pytest.mark.asyncio
    async def test_setup_tenant_monitoring(self, monitoring_service):
        tenant_id = "test-tenant-123"
        config = {"plan": "enterprise", "alert_rules": ["error_rate", "volume_spike"]}
        
        result = await monitoring_service.setup_tenant_monitoring(tenant_id, config)
        
        assert "dashboard" in result
        assert "alerts" in result
        assert result["dashboard"]["dashboard_id"] == f"dash-{tenant_id}"

    @pytest.mark.asyncio
    async def test_cleanup_tenant_monitoring(self, monitoring_service):
        tenant_id = "test-tenant-123"
        
        # First setup monitoring
        await monitoring_service.setup_tenant_monitoring(tenant_id, {"plan": "basic"})
        
        result = await monitoring_service.cleanup_tenant_monitoring(tenant_id)
        
        assert "final_metrics" in result
        assert "cleanup_completed_at" in result

class TestTenantOrchestrator:
    @pytest.mark.asyncio
    async def test_onboard_tenant_success(self, orchestrator):
        tenant_id = "test-tenant-123"
        tenant_data = {
            "name": "Test Organization",
            "email": "admin@test.com",
            "plan": "pro",
            "config": {"custom_setting": "value"}
        }
        
        with patch.object(orchestrator, '_update_tenant_state', new_callable=AsyncMock):
            result = await orchestrator.onboard_tenant(tenant_id, tenant_data)
        
        assert result["status"] == "completed"
        assert result["tenant_id"] == tenant_id
        assert "provisioning" in result
        assert "security" in result
        assert "monitoring" in result

    @pytest.mark.asyncio
    async def test_offboard_tenant_success(self, orchestrator):
        tenant_id = "test-tenant-123"
        
        with patch.object(orchestrator, '_update_tenant_state', new_callable=AsyncMock):
            result = await orchestrator.offboard_tenant(tenant_id)
        
        assert result["status"] == "completed"
        assert result["tenant_id"] == tenant_id
        assert "monitoring" in result
        assert "security" in result
        assert "provisioning" in result

    @pytest.mark.asyncio
    async def test_get_tenant_resources(self, orchestrator):
        tenant_id = "test-tenant-123"
        
        result = await orchestrator.get_tenant_resources(tenant_id)
        
        assert "storage_used_gb" in result
        assert "logs_ingested_today" in result
        assert "active_streams" in result
        assert "last_activity" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
