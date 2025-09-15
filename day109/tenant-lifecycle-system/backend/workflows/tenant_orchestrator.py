import asyncio
from typing import Dict, Any
from datetime import datetime

class TenantOrchestrator:
    """Orchestrates tenant lifecycle workflows"""
    
    def __init__(self, provisioning_service, security_service, monitoring_service):
        self.provisioning = provisioning_service
        self.security = security_service
        self.monitoring = monitoring_service
    
    async def onboard_tenant(self, tenant_id: str, tenant_data: Dict[str, Any]):
        """Complete tenant onboarding workflow"""
        print(f"🚀 Starting onboarding workflow for tenant {tenant_id}")
        
        try:
            # Step 1: Provision resources
            provisioning_result = await self.provisioning.provision_tenant_resources(
                tenant_id, tenant_data.get("plan", "basic"), tenant_data.get("config", {})
            )
            
            # Step 2: Setup security
            security_result = await self.security.setup_tenant_security(tenant_id, tenant_data)
            
            # Step 3: Configure monitoring
            monitoring_result = await self.monitoring.setup_tenant_monitoring(tenant_id, {
                **tenant_data.get("config", {}),
                "plan": tenant_data.get("plan", "basic")
            })
            
            # Step 4: Update tenant state to active
            await self._update_tenant_state(tenant_id, "active")
            
            print(f"✅ Onboarding completed for tenant {tenant_id}")
            
            return {
                "status": "completed",
                "tenant_id": tenant_id,
                "provisioning": provisioning_result,
                "security": security_result,
                "monitoring": monitoring_result,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Onboarding failed for tenant {tenant_id}: {str(e)}")
            await self._handle_onboarding_failure(tenant_id, str(e))
            raise
    
    async def offboard_tenant(self, tenant_id: str):
        """Complete tenant offboarding workflow"""
        print(f"👋 Starting offboarding workflow for tenant {tenant_id}")
        
        try:
            # Step 1: Suspend tenant operations
            await self._update_tenant_state(tenant_id, "suspended")
            await asyncio.sleep(5)  # Grace period for ongoing operations
            
            # Step 2: Cleanup monitoring
            monitoring_result = await self.monitoring.cleanup_tenant_monitoring(tenant_id)
            
            # Step 3: Revoke security credentials
            security_result = await self.security.revoke_tenant_security(tenant_id)
            
            # Step 4: Deprovision resources (with data archival)
            provisioning_result = await self.provisioning.deprovision_tenant_resources(tenant_id)
            
            # Step 5: Update tenant state to archived
            await self._update_tenant_state(tenant_id, "archived")
            
            print(f"✅ Offboarding completed for tenant {tenant_id}")
            
            return {
                "status": "completed",
                "tenant_id": tenant_id,
                "monitoring": monitoring_result,
                "security": security_result,
                "provisioning": provisioning_result,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Offboarding failed for tenant {tenant_id}: {str(e)}")
            raise
    
    async def get_tenant_resources(self, tenant_id: str) -> Dict[str, Any]:
        """Get current tenant resource allocation"""
        # In production, this would query actual resource usage
        return {
            "storage_used_gb": 2.5,
            "logs_ingested_today": 15000,
            "active_streams": 3,
            "last_activity": datetime.now().isoformat()
        }
    
    async def _update_tenant_state(self, tenant_id: str, new_state: str):
        """Update tenant state in database"""
        print(f"   📝 Updating tenant {tenant_id} state to {new_state}")
        # In production, update database record
        await asyncio.sleep(0.1)
    
    async def _handle_onboarding_failure(self, tenant_id: str, error: str):
        """Handle onboarding failure and cleanup partial resources"""
        print(f"   🔄 Rolling back partial onboarding for tenant {tenant_id}")
        
        # Attempt cleanup of any partially created resources
        try:
            await self.security.revoke_tenant_security(tenant_id)
        except:
            pass
        
        try:
            await self.monitoring.cleanup_tenant_monitoring(tenant_id)  
        except:
            pass
        
        await self._update_tenant_state(tenant_id, "failed")
