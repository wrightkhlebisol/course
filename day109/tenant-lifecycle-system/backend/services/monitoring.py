import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

class MonitoringService:
    """Handles tenant monitoring and metrics collection"""
    
    def __init__(self):
        self.tenant_metrics = {}
        self.activity_log = []
    
    async def setup_tenant_monitoring(self, tenant_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup monitoring for new tenant"""
        print(f"📊 Setting up monitoring for tenant {tenant_id}")
        
        # Initialize metrics collection
        self.tenant_metrics[tenant_id] = {
            "logs_ingested": 0,
            "queries_executed": 0,
            "storage_used_gb": 0,
            "last_activity": datetime.now(),
            "alerts_triggered": 0
        }
        
        # Setup dashboards
        dashboard_config = await self._create_tenant_dashboard(tenant_id)
        
        # Configure alerts
        alert_config = await self._configure_tenant_alerts(tenant_id, config)
        
        self._log_activity(f"Monitoring setup completed for tenant {tenant_id}")
        
        print(f"✅ Monitoring configured for tenant {tenant_id}")
        return {
            "dashboard": dashboard_config,
            "alerts": alert_config,
            "metrics_endpoint": f"/api/metrics/{tenant_id}"
        }
    
    async def _create_tenant_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Create monitoring dashboard for tenant"""
        await asyncio.sleep(0.1)  # Simulate async work
        return {
            "dashboard_id": f"dash-{tenant_id}",
            "url": f"/dashboard/{tenant_id}",
            "widgets": ["logs_volume", "error_rates", "performance_metrics"]
        }
    
    async def _configure_tenant_alerts(self, tenant_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure alerting for tenant"""
        await asyncio.sleep(0.1)  # Simulate async work
        return {
            "alert_rules": config.get("alert_rules", []),
            "notification_channels": ["email", "webhook"],
            "escalation_policy": "default"
        }
    
    async def cleanup_tenant_monitoring(self, tenant_id: str) -> Dict[str, Any]:
        """Remove monitoring for tenant"""
        print(f"🧹 Cleaning up monitoring for tenant {tenant_id}")
        
        # Archive metrics before cleanup
        if tenant_id in self.tenant_metrics:
            final_metrics = self.tenant_metrics[tenant_id].copy()
            del self.tenant_metrics[tenant_id]
        else:
            final_metrics = {}
        
        self._log_activity(f"Monitoring cleanup completed for tenant {tenant_id}")
        
        print(f"✅ Monitoring cleanup completed for tenant {tenant_id}")
        return {
            "final_metrics": final_metrics,
            "cleanup_completed_at": datetime.now().isoformat()
        }
    
    async def get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        return [
            {
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                "action": random.choice(["tenant_onboarded", "tenant_offboarded", "config_updated"]),
                "tenant_id": f"tenant-{random.randint(1, 10)}",
                "status": "completed"
            } for _ in range(5)
        ]
    
    def _log_activity(self, message: str):
        """Log system activity"""
        self.activity_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
        
        # Keep only last 100 entries
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[-100:]
