import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.core.alert_router import AlertRouter, AlertData, AlertSeverity, AlertSource

@pytest_asyncio.fixture
async def alert_router():
    incident_manager = AsyncMock()
    router = AlertRouter(incident_manager)
    await router.load_escalation_policies()
    return router

@pytest.mark.asyncio
async def test_alert_classification(alert_router):
    """Test alert classification logic"""
    alert_data = {
        "id": "test_alert_001",
        "title": "Database Connection Failed",
        "description": "Unable to connect to primary database",
        "source": "database",
        "severity": "critical",
        "service_name": "payment-service",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    result = await alert_router.process_alert(alert_data)
    
    assert result["success"] is True
    assert result["alert_id"] == "test_alert_001"
    assert result["processing_time_ms"] > 0

@pytest.mark.asyncio
async def test_routing_policy_selection(alert_router):
    """Test routing policy selection based on alert characteristics"""
    # Critical database alert should use critical_24x7 policy
    alert = AlertData(
        id="test_001",
        title="Test",
        description="Test",
        source=AlertSource.DATABASE,
        severity=AlertSeverity.CRITICAL,
        timestamp=datetime.now(timezone.utc),
        metadata={},
        tags=[],
        service_name="test-service"
    )
    
    policy = alert_router._get_routing_policy(alert)
    assert policy == "critical_24x7"

@pytest.mark.asyncio
async def test_service_catalog_enhancement(alert_router):
    """Test service catalog-based alert enhancement"""
    alert = AlertData(
        id="test_001",
        title="Test Alert",
        description="Test",
        source=AlertSource.APPLICATION,
        severity=AlertSeverity.MEDIUM,
        timestamp=datetime.now(timezone.utc),
        metadata={},
        tags=[],
        service_name="payment-service",  # Critical service in catalog
        team=None
    )
    
    enhanced_alert = await alert_router._classify_alert(alert)
    
    # Should be upgraded to HIGH severity due to critical service
    assert enhanced_alert.severity == AlertSeverity.HIGH
    assert enhanced_alert.team == "payments"
    assert "service-critical" in enhanced_alert.tags
