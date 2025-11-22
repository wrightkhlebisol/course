import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import httpx
from datetime import datetime, timezone

from src.integrations.incident_manager import IncidentManager
from src.core.alert_router import AlertData, AlertSeverity, AlertSource

@pytest_asyncio.fixture
async def incident_manager():
    manager = IncidentManager("test_pd_key", "test_og_key")
    # Mock HTTP clients
    manager.pagerduty_client = AsyncMock()
    manager.opsgenie_client = AsyncMock()
    return manager

@pytest.mark.asyncio
async def test_pagerduty_incident_creation(incident_manager):
    """Test PagerDuty incident creation"""
    # Mock successful API response
    mock_response = MagicMock()
    mock_response.json.return_value = {"incident": {"id": "INCIDENT123"}}
    incident_manager.pagerduty_client.post.return_value = mock_response
    
    alert_data = AlertData(
        id="test_001",
        title="Test Critical Alert",
        description="Test description",
        source=AlertSource.DATABASE,
        severity=AlertSeverity.CRITICAL,
        timestamp=datetime.now(timezone.utc),
        metadata={},
        tags=["test"],
        service_name="test-service"
    )
    
    incident_id = await incident_manager.create_pagerduty_incident(alert_data, {})
    
    assert incident_id == "INCIDENT123"
    assert incident_id in incident_manager.active_incidents
    assert incident_manager.active_incidents[incident_id]["provider"] == "pagerduty"

@pytest.mark.asyncio
async def test_opsgenie_alert_creation(incident_manager):
    """Test OpsGenie alert creation"""
    # Mock successful API response
    mock_response = MagicMock()
    mock_response.json.return_value = {"requestId": "ALERT456"}
    incident_manager.opsgenie_client.post.return_value = mock_response
    
    alert_data = AlertData(
        id="test_002",
        title="Test High Alert",
        description="Test description",
        source=AlertSource.API,
        severity=AlertSeverity.HIGH,
        timestamp=datetime.now(timezone.utc),
        metadata={},
        tags=["api", "high"],
        service_name="api-gateway"
    )
    
    alert_id = await incident_manager.create_opsgenie_incident(alert_data, {})
    
    assert alert_id == "ALERT456"
    assert alert_id in incident_manager.active_incidents
    assert incident_manager.active_incidents[alert_id]["provider"] == "opsgenie"

@pytest.mark.asyncio
async def test_api_error_handling(incident_manager):
    """Test API error handling"""
    # Mock HTTP error
    incident_manager.pagerduty_client.post.side_effect = httpx.HTTPStatusError(
        "API Error", request=MagicMock(), response=MagicMock()
    )
    
    alert_data = AlertData(
        id="test_003",
        title="Test Alert",
        description="Test",
        source=AlertSource.APPLICATION,
        severity=AlertSeverity.MEDIUM,
        timestamp=datetime.now(timezone.utc),
        metadata={},
        tags=[],
        service_name="test-service"
    )
    
    with pytest.raises(Exception):
        await incident_manager.create_pagerduty_incident(alert_data, {})
