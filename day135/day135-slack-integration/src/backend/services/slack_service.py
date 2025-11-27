import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import redis
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.alert import LogAlert, SlackMessage, NotificationStatus, AlertStatus, AlertSeverity
from ..config.config import settings

logger = structlog.get_logger(__name__)

class SlackService:
    def __init__(self):
        self.client = AsyncWebClient(token=settings.slack_bot_token)
        self.redis_client = redis.from_url(settings.redis_url)
        self.rate_limiter = RateLimiter(settings.max_alerts_per_minute)
        self.deduplicator = AlertDeduplicator(settings.deduplication_window_minutes)
        
    async def send_alert(self, alert: LogAlert) -> NotificationStatus:
        """Send alert to appropriate Slack channel(s)"""
        try:
            # Check deduplication
            if self.deduplicator.is_duplicate(alert):
                logger.info("Skipping duplicate alert", alert_id=alert.id)
                return NotificationStatus(
                    alert_id=alert.id,
                    status=AlertStatus.PENDING,
                    channel="duplicate"
                )
            
            # Rate limiting
            if not await self.rate_limiter.allow_request():
                logger.warning("Rate limit exceeded, queuing alert", alert_id=alert.id)
                await self._queue_alert(alert)
                return NotificationStatus(
                    alert_id=alert.id,
                    status=AlertStatus.PENDING,
                    channel="queued"
                )
            
            # Determine target channels
            channels = self._resolve_channels(alert)
            
            # Format message
            slack_message = self._format_alert_message(alert)
            
            # Send to channels
            notification_statuses = []
            for channel in channels:
                status = await self._send_to_channel(alert, slack_message, channel)
                notification_statuses.append(status)
            
            # Store notification record (always store, even if sending failed)
            if notification_statuses:
                await self._store_notification(alert, notification_statuses)
            else:
                # Store a failed notification record
                failed_status = NotificationStatus(
                    alert_id=alert.id,
                    status=AlertStatus.FAILED,
                    channel="none"
                )
                await self._store_notification(alert, [failed_status])
            
            return notification_statuses[0] if notification_statuses else NotificationStatus(
                alert_id=alert.id,
                status=AlertStatus.FAILED,
                channel="none"
            )
            
        except Exception as e:
            logger.error("Failed to send alert", alert_id=alert.id, error=str(e))
            # Store failed notification
            failed_status = NotificationStatus(
                alert_id=alert.id,
                status=AlertStatus.FAILED,
                channel="error",
                error_message=str(e)
            )
            try:
                await self._store_notification(alert, [failed_status])
            except Exception as store_error:
                logger.error("Failed to store notification record", error=str(store_error))
            
            return failed_status
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _send_to_channel(self, alert: LogAlert, message: SlackMessage, channel: str) -> NotificationStatus:
        """Send message to specific Slack channel with retry logic"""
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=message.text,
                blocks=message.blocks,
                attachments=message.attachments
            )
            
            return NotificationStatus(
                alert_id=alert.id,
                status=AlertStatus.SENT,
                channel=channel,
                message_ts=response["ts"],
                sent_at=datetime.now()
            )
            
        except SlackApiError as e:
            if e.response["error"] == "channel_not_found":
                logger.warning("Channel not found, using default", channel=channel)
                return await self._send_to_channel(alert, message, settings.default_channel)
            raise
    
    def _resolve_channels(self, alert: LogAlert) -> List[str]:
        """Determine which channels should receive this alert"""
        channels = []
        
        # Service-based routing
        service_channel = settings.channel_routing.get(alert.service)
        if service_channel:
            channels.append(service_channel)
        
        # Severity-based routing
        severity_channels = settings.severity_channels.get(alert.severity.value, [])
        channels.extend(severity_channels)
        
        # Default channel if no specific routing
        if not channels:
            channels.append(settings.default_channel)
        
        return list(set(channels))  # Remove duplicates
    
    def _format_alert_message(self, alert: LogAlert) -> SlackMessage:
        """Format alert as Slack message with blocks and interactions"""
        
        # Determine color based on severity
        color_map = {
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.ERROR: "#ff9900", 
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.INFO: "#36a64f"
        }
        
        # Create rich message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {alert.severity.value.upper()}: {alert.title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.message
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Service:*\n{alert.service}"
                    },
                    {
                        "type": "mrkdwn", 
                        "text": f"*Component:*\n{alert.component}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
        
        # Add affected users if available
        if alert.affected_users:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"👥 *Affected Users:* {alert.affected_users:,}"
                }
            })
        
        # Add action buttons
        actions = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Acknowledge"
                    },
                    "style": "primary",
                    "action_id": f"ack_{alert.id}",
                    "value": alert.id
                }
            ]
        }
        
        # Add links if available
        if alert.dashboard_url or alert.runbook_url:
            links = []
            if alert.dashboard_url:
                links.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Dashboard"
                    },
                    "url": alert.dashboard_url,
                    "action_id": f"dashboard_{alert.id}"
                })
            
            if alert.runbook_url:
                links.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text", 
                        "text": "📖 Runbook"
                    },
                    "url": alert.runbook_url,
                    "action_id": f"runbook_{alert.id}"
                })
            
            actions["elements"].extend(links)
        
        blocks.append(actions)
        
        return SlackMessage(
            channel="",  # Will be set by caller
            text=f"{alert.severity.value.upper()}: {alert.title} - {alert.message}",
            blocks=blocks
        )
    
    async def handle_interaction(self, payload: Dict) -> Dict:
        """Handle Slack interactive components (button clicks)"""
        try:
            action_id = payload["actions"][0]["action_id"]
            user_id = payload["user"]["id"]
            
            if action_id.startswith("ack_"):
                alert_id = action_id.replace("ack_", "")
                await self._acknowledge_alert(alert_id, user_id)
                
                return {
                    "response_type": "ephemeral",
                    "text": f"✅ Alert {alert_id} acknowledged by <@{user_id}>"
                }
            
            return {"response_type": "ephemeral", "text": "Unknown action"}
            
        except Exception as e:
            logger.error("Failed to handle interaction", error=str(e))
            return {"response_type": "ephemeral", "text": "Failed to process action"}
    
    async def _acknowledge_alert(self, alert_id: str, user_id: str):
        """Mark alert as acknowledged"""
        key = f"alert_status:{alert_id}"
        status_data = {
            "status": AlertStatus.ACKNOWLEDGED.value,
            "acknowledged_by": user_id,
            "acknowledged_at": datetime.now().isoformat()
        }
        self.redis_client.hset(key, mapping=status_data)
        logger.info("Alert acknowledged", alert_id=alert_id, user=user_id)
    
    async def _queue_alert(self, alert: LogAlert):
        """Queue alert for later delivery"""
        queue_key = "alert_queue"
        alert_data = alert.json()
        self.redis_client.lpush(queue_key, alert_data)
    
    async def _store_notification(self, alert: LogAlert, statuses: List[NotificationStatus]):
        """Store notification records in Redis"""
        for status in statuses:
            key = f"notification:{alert.id}:{status.channel}"
            data = status.dict()
            # Convert all values to strings for Redis, handling enums properly
            redis_data = {}
            for k, v in data.items():
                if v is None:
                    redis_data[k] = ""
                elif hasattr(v, 'value'):  # Enum type
                    redis_data[k] = str(v.value)
                elif isinstance(v, datetime):
                    redis_data[k] = v.isoformat()
                else:
                    redis_data[k] = str(v)
            self.redis_client.hset(key, mapping=redis_data)
            self.redis_client.expire(key, 86400 * 7)  # 7 days retention

class RateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.redis_client = redis.from_url(settings.redis_url)
    
    async def allow_request(self) -> bool:
        """Check if request is within rate limit"""
        key = "slack_rate_limit"
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        results = pipe.execute()
        
        current_count = results[0]
        return current_count <= self.requests_per_minute

class AlertDeduplicator:
    def __init__(self, window_minutes: int):
        self.window_minutes = window_minutes
        self.redis_client = redis.from_url(settings.redis_url)
    
    def is_duplicate(self, alert: LogAlert) -> bool:
        """Check if alert is a duplicate within the time window"""
        # Create hash of alert content
        content_hash = hashlib.md5(
            f"{alert.service}:{alert.component}:{alert.title}".encode()
        ).hexdigest()
        
        key = f"alert_dedup:{content_hash}"
        
        if self.redis_client.exists(key):
            return True
        
        # Set with expiration
        self.redis_client.setex(key, self.window_minutes * 60, "1")
        return False
