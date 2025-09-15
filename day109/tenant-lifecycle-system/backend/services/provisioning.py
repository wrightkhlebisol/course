import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

class ProvisioningService:
    """Handles tenant resource provisioning and cleanup"""
    
    def __init__(self):
        self.base_config_path = "config/tenant_configs"
        self.resource_templates = self._load_resource_templates()
    
    def _load_resource_templates(self) -> Dict[str, Any]:
        """Load resource allocation templates"""
        return {
            "basic": {
                "log_retention_days": 30,
                "max_ingestion_rate": 1000,
                "storage_quota_gb": 10,
                "alert_rules": ["error_rate_5min", "volume_spike"]
            },
            "pro": {
                "log_retention_days": 90,
                "max_ingestion_rate": 5000,
                "storage_quota_gb": 100,
                "alert_rules": ["error_rate_5min", "volume_spike", "latency_p95"]
            },
            "enterprise": {
                "log_retention_days": 365,
                "max_ingestion_rate": 50000,
                "storage_quota_gb": 1000,
                "alert_rules": ["error_rate_5min", "volume_spike", "latency_p95", "custom_business_rules"]
            }
        }
    
    async def provision_tenant_resources(self, tenant_id: str, plan: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision all resources for a new tenant"""
        print(f"🔧 Provisioning resources for tenant {tenant_id} with plan {plan}")
        
        resources = self.resource_templates.get(plan, self.resource_templates["basic"])
        
        # Create tenant-specific directories
        tenant_dir = f"data/tenants/{tenant_id}"
        os.makedirs(f"{tenant_dir}/logs", exist_ok=True)
        os.makedirs(f"{tenant_dir}/config", exist_ok=True)
        os.makedirs(f"{tenant_dir}/metrics", exist_ok=True)
        
        # Create tenant configuration file
        tenant_config = {
            **resources,
            **config,
            "tenant_id": tenant_id,
            "provisioned_at": datetime.now().isoformat(),
            "namespace": f"tenant-{tenant_id}",
            "data_path": tenant_dir
        }
        
        with open(f"{tenant_dir}/config/tenant.json", "w") as f:
            json.dump(tenant_config, f, indent=2)
        
        # Simulate resource allocation
        await self._create_log_streams(tenant_id, resources)
        await self._setup_monitoring(tenant_id, resources)
        await self._configure_alerts(tenant_id, resources)
        
        print(f"✅ Resources provisioned for tenant {tenant_id}")
        return {
            "status": "provisioned",
            "resources": resources,
            "config_path": f"{tenant_dir}/config/tenant.json"
        }
    
    async def _create_log_streams(self, tenant_id: str, resources: Dict[str, Any]):
        """Create isolated log processing streams"""
        await asyncio.sleep(0.1)  # Simulate async work
        print(f"   📊 Created log streams with {resources['max_ingestion_rate']}/sec capacity")
    
    async def _setup_monitoring(self, tenant_id: str, resources: Dict[str, Any]):
        """Setup tenant-specific monitoring"""
        await asyncio.sleep(0.1)  # Simulate async work
        print(f"   📈 Configured monitoring with {resources['log_retention_days']} days retention")
    
    async def _configure_alerts(self, tenant_id: str, resources: Dict[str, Any]):
        """Configure alerting rules"""
        await asyncio.sleep(0.1)  # Simulate async work
        print(f"   🚨 Configured {len(resources['alert_rules'])} alert rules")
    
    async def deprovision_tenant_resources(self, tenant_id: str) -> Dict[str, Any]:
        """Clean up all tenant resources"""
        print(f"🧹 Deprovisioning resources for tenant {tenant_id}")
        
        tenant_dir = f"data/tenants/{tenant_id}"
        
        # Archive data before cleanup (respecting retention policies)
        archive_result = await self._archive_tenant_data(tenant_id)
        
        # Remove tenant directories (in real implementation, would be more careful)
        if os.path.exists(tenant_dir):
            import shutil
            shutil.rmtree(tenant_dir)
        
        print(f"✅ Resources deprovisioned for tenant {tenant_id}")
        return {
            "status": "deprovisioned",
            "archived": archive_result["archived"],
            "cleanup_completed_at": datetime.now().isoformat()
        }
    
    async def _archive_tenant_data(self, tenant_id: str) -> Dict[str, Any]:
        """Archive tenant data according to retention policies"""
        await asyncio.sleep(0.2)  # Simulate archival work
        return {
            "archived": True,
            "archive_location": f"archive/tenant-{tenant_id}-{datetime.now().strftime('%Y%m%d')}",
            "retention_expires": "2026-06-01"  # Example retention date
        }
