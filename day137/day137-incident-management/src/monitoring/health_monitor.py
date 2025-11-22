"""
Health Monitor - Monitor integration health and performance metrics
Tracks API connectivity, response times, and system health
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from collections import deque, defaultdict

import structlog

logger = structlog.get_logger()

class HealthMonitor:
    """Monitors system health and integration performance"""
    
    def __init__(self, incident_manager):
        self.incident_manager = incident_manager
        self.metrics = {
            "alerts_processed": 0,
            "incidents_created": 0,
            "api_errors": defaultdict(int),
            "response_times": defaultdict(deque),
            "webhook_events": 0,
            "system_status": "healthy"
        }
        self.health_checks = {}
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """Start background health monitoring"""
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(60)
    
    async def _perform_health_checks(self):
        """Perform periodic health checks"""
        current_time = datetime.now()
        
        # Check if integrations are configured with valid API keys (not test/demo keys)
        pd_api_key = self.incident_manager.pagerduty_api_key or ""
        og_api_key = self.incident_manager.opsgenie_api_key or ""
        
        pd_configured = (
            self.incident_manager.settings.enable_pagerduty 
            and self.incident_manager.pagerduty_client
            and pd_api_key
            and not pd_api_key.startswith("test_")
            and not pd_api_key.startswith("demo_")
            and len(pd_api_key) > 10
        )
        og_configured = (
            self.incident_manager.settings.enable_opsgenie 
            and self.incident_manager.opsgenie_client
            and og_api_key
            and not og_api_key.startswith("test_")
            and not og_api_key.startswith("demo_")
            and len(og_api_key) > 10
        )
        
        # Check PagerDuty connectivity
        if pd_configured:
            pd_health = await self._check_pagerduty_health()
            self.health_checks["pagerduty"] = {
                "healthy": pd_health,
                "last_check": current_time,
                "response_time_ms": 0,
                "configured": True
            }
        else:
            self.health_checks["pagerduty"] = {
                "healthy": None,
                "last_check": current_time,
                "response_time_ms": 0,
                "configured": False
            }
        
        # Check OpsGenie connectivity  
        if og_configured:
            og_health = await self._check_opsgenie_health()
            self.health_checks["opsgenie"] = {
                "healthy": og_health,
                "last_check": current_time,
                "response_time_ms": 0,
                "configured": True
            }
        else:
            self.health_checks["opsgenie"] = {
                "healthy": None,
                "last_check": current_time,
                "response_time_ms": 0,
                "configured": False
            }
        
        # Update overall system status
        # Only mark as degraded if configured integrations are failing
        configured_checks = [check for check in self.health_checks.values() if check.get("configured", False)]
        if not configured_checks:
            # No integrations configured - system is operational with local incidents
            self.metrics["system_status"] = "operational"
        else:
            all_healthy = all(check["healthy"] for check in configured_checks)
            self.metrics["system_status"] = "healthy" if all_healthy else "degraded"
        
        logger.debug("Health check completed", 
                    pagerduty=pd_health if pd_configured else "not_configured",
                    opsgenie=og_health if og_configured else "not_configured")
    
    async def _check_pagerduty_health(self) -> bool:
        """Check PagerDuty API health"""
        try:
            if not self.incident_manager.pagerduty_client:
                return False
            
            start_time = time.time()
            response = await self.incident_manager.pagerduty_client.get("/users", params={"limit": 1})
            response_time = time.time() - start_time
            
            # Track response time
            self.metrics["response_times"]["pagerduty"].append(response_time * 1000)
            # Keep only last 100 measurements
            if len(self.metrics["response_times"]["pagerduty"]) > 100:
                self.metrics["response_times"]["pagerduty"].popleft()
            
            return response.status_code == 200
            
        except Exception as e:
            self.metrics["api_errors"]["pagerduty"] += 1
            logger.debug("PagerDuty health check failed", error=str(e))
            return False
    
    async def _check_opsgenie_health(self) -> bool:
        """Check OpsGenie API health"""
        try:
            if not self.incident_manager.opsgenie_client:
                return False
            
            start_time = time.time()
            response = await self.incident_manager.opsgenie_client.get("/account")
            response_time = time.time() - start_time
            
            # Track response time
            self.metrics["response_times"]["opsgenie"].append(response_time * 1000)
            if len(self.metrics["response_times"]["opsgenie"]) > 100:
                self.metrics["response_times"]["opsgenie"].popleft()
            
            return response.status_code == 200
            
        except Exception as e:
            self.metrics["api_errors"]["opsgenie"] += 1
            logger.debug("OpsGenie health check failed", error=str(e))
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        # Re-check configuration status in real-time
        # Get API keys from settings (source of truth)
        from core.config import get_settings
        settings = get_settings()
        pd_api_key = str(settings.pagerduty_api_key) if settings.pagerduty_api_key else ""
        og_api_key = str(settings.opsgenie_api_key) if settings.opsgenie_api_key else ""
        
        # Check if keys are test/demo/placeholder keys
        pd_is_test_key = (
            pd_api_key.startswith("test_") 
            or pd_api_key.startswith("demo_") 
            or "your_" in pd_api_key.lower()
            or pd_api_key in ["test_pd_key", ""]
            or len(pd_api_key) <= 10
        )
        og_is_test_key = (
            og_api_key.startswith("test_") 
            or og_api_key.startswith("demo_") 
            or "your_" in og_api_key.lower()
            or og_api_key in ["test_og_key", ""]
            or len(og_api_key) <= 10
        )
        
        pd_configured = (
            self.incident_manager.settings.enable_pagerduty 
            and self.incident_manager.pagerduty_client
            and pd_api_key
            and not pd_is_test_key
        )
        og_configured = (
            self.incident_manager.settings.enable_opsgenie 
            and self.incident_manager.opsgenie_client
            and og_api_key
            and not og_is_test_key
        )
        
        logger.debug("Health status check", 
                    pd_key_length=len(pd_api_key),
                    pd_is_test=pd_is_test_key,
                    pd_configured=pd_configured,
                    og_key_length=len(og_api_key),
                    og_is_test=og_is_test_key,
                    og_configured=og_configured)
        
        pd_check = self.health_checks.get("pagerduty", {})
        og_check = self.health_checks.get("opsgenie", {})
        
        # Determine status for each integration
        pd_status = None
        if not pd_configured:
            pd_status = None  # Not configured
        else:
            pd_status = pd_check.get("healthy", False)
        
        og_status = None
        if not og_configured:
            og_status = None  # Not configured
        else:
            og_status = og_check.get("healthy", False)
        
        # Update system status based on actual configuration
        configured_checks = []
        if pd_configured:
            configured_checks.append(pd_status)
        if og_configured:
            configured_checks.append(og_status)
        
        if not configured_checks:
            system_status = "operational"
        else:
            system_status = "healthy" if all(configured_checks) else "degraded"
        
        return {
            "system_status": system_status,
            "timestamp": datetime.now().isoformat(),
            "integrations": self.health_checks,
            "active_incidents": len(self.incident_manager.active_incidents),
            "uptime_checks": {
                "pagerduty": pd_status,
                "opsgenie": og_status
            },
            "integration_status": {
                "pagerduty": {
                    "configured": pd_configured,
                    "healthy": pd_status
                },
                "opsgenie": {
                    "configured": og_configured,
                    "healthy": og_status
                }
            }
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics"""
        # Calculate average response times
        avg_response_times = {}
        for provider, times in self.metrics["response_times"].items():
            if times:
                avg_response_times[f"{provider}_avg_ms"] = sum(times) / len(times)
            else:
                avg_response_times[f"{provider}_avg_ms"] = 0
        
        return {
            "alerts_processed": self.metrics["alerts_processed"],
            "incidents_created": self.metrics["incidents_created"],
            "webhook_events": self.metrics["webhook_events"],
            "api_errors": dict(self.metrics["api_errors"]),
            "average_response_times": avg_response_times,
            "active_incidents": len(self.incident_manager.active_incidents),
            "system_status": self.metrics["system_status"],
            "timestamp": datetime.now().isoformat()
        }
    
    def record_alert_processed(self):
        """Record alert processing metric"""
        self.metrics["alerts_processed"] += 1
    
    def record_incident_created(self):
        """Record incident creation metric"""
        self.metrics["incidents_created"] += 1
    
    def record_webhook_event(self):
        """Record webhook event metric"""
        self.metrics["webhook_events"] += 1
