import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

from src.backend.models.alert import LogAlert, AlertSeverity, AlertStatus
from src.backend.services.slack_service import SlackService, RateLimiter, AlertDeduplicator

@pytest.fixture
def sample_alert():
    return LogAlert(
        id="test-alert-123",
        title="Test Alert",
        message="This is a test alert message",
        severity=AlertSeverity.ERROR,
        service="payment",
        component="processor",
        timestamp=datetime.now(),
        metadata={"test": True},
        dashboard_url="https://dashboard.example.com",
        runbook_url="https://runbook.example.com"
    )

@pytest.fixture
def mock_slack_service():
    with patch('src.backend.services.slack_service.AsyncWebClient') as mock_client, \
         patch('src.backend.services.slack_service.redis.from_url') as mock_redis:
        
        mock_redis.return_value.ping.return_value = True
        service = SlackService()
        service.client.chat_postMessage = AsyncMock(return_value={"ts": "1234567890.123456"})
        return service

class TestSlackService:
    @pytest.mark.asyncio
    async def test_send_alert_success(self, mock_slack_service, sample_alert):
        """Test successful alert sending"""
        status = await mock_slack_service.send_alert(sample_alert)
        
        assert status.alert_id == sample_alert.id
        assert status.status == AlertStatus.SENT
        mock_slack_service.client.chat_postMessage.assert_called_once()

    @pytest.mark.asyncio 
    async def test_channel_resolution(self, mock_slack_service, sample_alert):
        """Test proper channel resolution based on service"""
        channels = mock_slack_service._resolve_channels(sample_alert)
        
        # Should include service-specific channel for payment service
        assert "#payments-team" in channels
        # Should include severity-specific channel for error
        assert "#alerts" in channels

    def test_message_formatting(self, mock_slack_service, sample_alert):
        """Test Slack message formatting"""
        message = mock_slack_service._format_alert_message(sample_alert)
        
        assert message.text.startswith("ERROR:")
        assert len(message.blocks) > 0
        
        # Check for action buttons
        action_block = next((block for block in message.blocks if block["type"] == "actions"), None)
        assert action_block is not None
        assert any(element["action_id"].startswith("ack_") for element in action_block["elements"])

    @pytest.mark.asyncio
    async def test_interaction_handling(self, mock_slack_service):
        """Test handling of Slack interactions"""
        payload = {
            "actions": [{"action_id": "ack_test-alert-123", "value": "test-alert-123"}],
            "user": {"id": "U123456"}
        }
        
        response = await mock_slack_service.handle_interaction(payload)
        
        assert response["response_type"] == "ephemeral"
        assert "acknowledged" in response["text"]

class TestRateLimiter:
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        with patch('src.backend.services.slack_service.redis.from_url') as mock_redis:
            mock_redis.return_value.pipeline.return_value.execute.return_value = [5, True]
            
            limiter = RateLimiter(requests_per_minute=10)
            result = asyncio.run(limiter.allow_request())
            
            assert result is True

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario"""
        with patch('src.backend.services.slack_service.redis.from_url') as mock_redis:
            mock_redis.return_value.pipeline.return_value.execute.return_value = [15, True]
            
            limiter = RateLimiter(requests_per_minute=10)
            result = asyncio.run(limiter.allow_request())
            
            assert result is False

class TestAlertDeduplicator:
    def test_duplicate_detection(self, sample_alert):
        """Test duplicate alert detection"""
        with patch('src.backend.services.slack_service.redis.from_url') as mock_redis:
            mock_redis.return_value.exists.return_value = True
            
            deduplicator = AlertDeduplicator(window_minutes=5)
            is_duplicate = deduplicator.is_duplicate(sample_alert)
            
            assert is_duplicate is True

    def test_new_alert_detection(self, sample_alert):
        """Test new alert detection"""
        with patch('src.backend.services.slack_service.redis.from_url') as mock_redis:
            mock_redis.return_value.exists.return_value = False
            
            deduplicator = AlertDeduplicator(window_minutes=5)
            is_duplicate = deduplicator.is_duplicate(sample_alert)
            
            assert is_duplicate is False
            mock_redis.return_value.setex.assert_called_once()

class TestIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_alert_flow(self, sample_alert):
        """Test complete alert processing flow"""
        with patch('src.backend.services.slack_service.AsyncWebClient') as mock_client, \
             patch('src.backend.services.slack_service.redis.from_url') as mock_redis:
            
            # Setup mocks
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.exists.return_value = False  # Not duplicate
            mock_redis.return_value.pipeline.return_value.execute.return_value = [1, True]  # Within rate limit
            
            mock_client.return_value.chat_postMessage = AsyncMock(
                return_value={"ts": "1234567890.123456"}
            )
            
            # Create service and send alert
            service = SlackService()
            status = await service.send_alert(sample_alert)
            
            # Verify results
            assert status.status == AlertStatus.SENT
            assert status.message_ts == "1234567890.123456"
            mock_client.return_value.chat_postMessage.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
