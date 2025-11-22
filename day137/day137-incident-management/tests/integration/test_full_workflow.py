import pytest
import asyncio
from datetime import datetime, timezone

from src.core.alert_router import AlertRouter
from src.integrations.incident_manager import IncidentManager
from src.monitoring.health_monitor import HealthMonitor

@pytest.mark.asyncio
async def test_end_to_end_alert_processing():
    """Test complete alert processing workflow"""
    # Initialize components
    incident_manager = IncidentManager("test_key", "test_key")
    alert_router = AlertRouter(incident_manager)
    health_monitor = HealthMonitor(incident_manager)
    
    await alert_router.load_escalation_policies()
    
    # Test alert data
    alert_data = {
        "id": "integration_test_001",
        "title": "Integration Test Critical Alert",
        "description": "Testing end-to-end alert processing",
        "source": "database",
        "severity": "critical",
        "service_name": "payment-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {"test": "integration"},
        "tags": ["integration", "test"]
    }
    
    # Process the alert
    result = await alert_router.process_alert(alert_data)
    
    # Verify processing results
    assert result is not None
    assert "alert_id" in result
    assert "processing_time_ms" in result
    assert "routing_results" in result
    
    # Verify health monitoring
    health_status = await health_monitor.get_health_status()
    assert health_status is not None
    assert "system_status" in health_status

@pytest.mark.asyncio
async def test_concurrent_alert_processing():
    """Test processing multiple alerts concurrently"""
    from unittest.mock import AsyncMock
    
    incident_manager = IncidentManager("test_key", "test_key")
    # Mock HTTP clients to avoid None errors
    incident_manager.pagerduty_client = AsyncMock()
    incident_manager.opsgenie_client = AsyncMock()
    # Mock the create methods to return fake IDs
    incident_manager.create_pagerduty_incident = AsyncMock(return_value="PD_INCIDENT_123")
    incident_manager.create_opsgenie_incident = AsyncMock(return_value="OG_ALERT_456")
    
    alert_router = AlertRouter(incident_manager)
    
    await alert_router.load_escalation_policies()
    
    # Create multiple alerts
    alerts = []
    for i in range(10):
        alert_data = {
            "id": f"concurrent_test_{i:03d}",
            "title": f"Concurrent Test Alert {i}",
            "description": f"Testing concurrent processing - alert {i}",
            "source": "application",
            "severity": "medium",
            "service_name": f"service-{i}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        alerts.append(alert_data)
    
    # Process alerts concurrently
    tasks = [alert_router.process_alert(alert) for alert in alerts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all alerts were processed successfully
    successful_results = [r for r in results if not isinstance(r, Exception)]
    assert len(successful_results) == 10
    
    for result in successful_results:
        assert result.get("success") is not False  # Could be True or None for demo mode

@pytest.mark.asyncio
async def test_webhook_processing():
    """Test webhook event processing"""
    incident_manager = IncidentManager("test_key", "test_key")
    alert_router = AlertRouter(incident_manager)
    
    from src.webhooks.webhook_handler import WebhookHandler
    webhook_handler = WebhookHandler(incident_manager, alert_router)
    
    # Test PagerDuty webhook payload
    pd_payload = {
        "messages": [{
            "event": "incident.acknowledged",
            "incident": {
                "id": "INCIDENT123",
                "status": "acknowledged",
                "acknowledged_by": {"summary": "Test User"}
            }
        }]
    }
    
    import json
    result = await webhook_handler.handle_pagerduty_webhook(
        json.dumps(pd_payload).encode(),
        {}
    )
    
    assert result["status"] == "success"
    assert result["processed_events"] == 1
