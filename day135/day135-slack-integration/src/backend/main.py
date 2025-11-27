from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import structlog
from typing import List, Dict
from datetime import datetime

from .services.slack_service import SlackService
from .services.alert_generator import AlertGenerator
from .models.alert import LogAlert, AlertSeverity, NotificationStatus
from .config.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Slack Notification Integration",
    description="Real-time Slack notifications for distributed log processing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
slack_service = SlackService()
alert_generator = AlertGenerator()
redis_client = redis.from_url(settings.redis_url)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Slack Integration Service")
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))

@app.post("/api/alerts/send")
async def send_alert(alert: LogAlert, background_tasks: BackgroundTasks):
    """Send alert to Slack"""
    try:
        logger.info("Received alert", alert_id=alert.id, severity=alert.severity)
        
        background_tasks.add_task(process_alert, alert)
        
        return {
            "status": "accepted",
            "alert_id": alert.id,
            "message": "Alert queued for processing"
        }
    except Exception as e:
        logger.error("Failed to queue alert", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process alert")

async def process_alert(alert: LogAlert):
    """Process alert in background"""
    try:
        status = await slack_service.send_alert(alert)
        logger.info("Alert processed", alert_id=alert.id, status=status.status)
    except Exception as e:
        logger.error("Failed to process alert", alert_id=alert.id, error=str(e))

@app.post("/api/alerts/test")
async def generate_test_alert(severity: AlertSeverity = AlertSeverity.INFO):
    """Generate and send test alert"""
    try:
        alert = alert_generator.generate_alert(severity)
        
        # Check if Slack is configured (check for non-empty, non-placeholder values)
        token_valid = settings.slack_bot_token and settings.slack_bot_token.strip() and not settings.slack_bot_token.startswith('xoxb-your-')
        webhook_valid = settings.slack_webhook_url and settings.slack_webhook_url.strip() and 'hooks.slack.com' in settings.slack_webhook_url and not 'YOUR/WEBHOOK' in settings.slack_webhook_url
        slack_configured = token_valid or webhook_valid
        
        if not slack_configured:
            # Demo mode: simulate successful send without actually sending to Slack
            logger.info("Slack not configured, running in demo mode", alert_id=alert.id)
            
            # Determine channel based on severity (same logic as SlackService)
            from .models.alert import AlertStatus
            severity_channels = settings.severity_channels.get(severity.value, [])
            channel = severity_channels[0] if severity_channels else settings.default_channel
            
            # Create a simulated successful notification status
            demo_status = NotificationStatus(
                alert_id=alert.id,
                status=AlertStatus.SENT,
                channel=channel,
                sent_at=datetime.now()
            )
            
            # Store the notification
            await slack_service._store_notification(alert, [demo_status])
            
            return {
                "alert": alert.dict(),
                "status": demo_status.dict()
            }
        else:
            # Real mode: actually send to Slack
            status = await slack_service.send_alert(alert)
            return {
                "alert": alert.dict(),
                "status": status.dict()
            }
    except Exception as e:
        logger.error("Failed to generate test alert", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate test alert")

@app.post("/api/slack/interactions")
async def handle_slack_interaction(request: Request):
    """Handle Slack interactive components"""
    try:
        form = await request.form()
        payload = json.loads(form["payload"])
        
        response = await slack_service.handle_interaction(payload)
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error("Failed to handle Slack interaction", error=str(e))
        return JSONResponse(content={"text": "Failed to process interaction"})

@app.get("/api/stats")
async def get_stats():
    """Get notification statistics"""
    try:
        # Test Redis connection first
        redis_client.ping()
        
        # Get rate limit stats
        rate_limit_key = "slack_rate_limit"
        current_rate = redis_client.get(rate_limit_key) or 0
        
        # Get recent alerts
        alert_keys = redis_client.keys("notification:*")
        recent_alerts = len(alert_keys)
        
        # Get queue depth
        queue_depth = redis_client.llen("alert_queue")
        
        return {
            "current_rate_per_minute": int(current_rate),
            "max_rate_per_minute": settings.max_alerts_per_minute,
            "recent_notifications": recent_alerts,
            "queued_alerts": queue_depth,
            "deduplication_window_minutes": settings.deduplication_window_minutes,
            "timestamp": datetime.now().isoformat()
        }
    except redis.ConnectionError as e:
        logger.warning("Redis not available, returning default stats", error=str(e))
        # Return default values when Redis is unavailable
        return {
            "current_rate_per_minute": 0,
            "max_rate_per_minute": settings.max_alerts_per_minute,
            "recent_notifications": 0,
            "queued_alerts": 0,
            "deduplication_window_minutes": settings.deduplication_window_minutes,
            "timestamp": datetime.now().isoformat(),
            "redis_unavailable": True
        }
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.get("/api/notifications/recent")
async def get_recent_notifications(limit: int = 20):
    """Get recent notification history"""
    try:
        # Test Redis connection first
        redis_client.ping()
        
        # Use SCAN instead of KEYS for better performance with large datasets
        notification_keys = []
        cursor = 0
        pattern = "notification:*"
        max_iterations = 10  # Limit iterations to prevent long queries
        
        for _ in range(max_iterations):
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            notification_keys.extend(keys)
            if cursor == 0 or len(notification_keys) >= limit * 2:  # Get a bit more than needed
                break
        
        # Sort by key (which includes timestamp in alert ID) and take most recent
        notification_keys = sorted(notification_keys, reverse=True)[:limit]
        notifications = []
        
        for key in notification_keys:
            data = redis_client.hgetall(key)
            if data:
                # Decode bytes to strings
                decoded_data = {k.decode(): v.decode() for k, v in data.items()}
                # Normalize status - remove "AlertStatus." prefix if present
                status = decoded_data.get("status", "")
                if status.startswith("AlertStatus."):
                    status = status.replace("AlertStatus.", "").lower()
                
                notifications.append({
                    "key": key.decode(),
                    "alert_id": decoded_data.get("alert_id", ""),
                    "status": status,
                    "channel": decoded_data.get("channel", ""),
                    "sent_at": decoded_data.get("sent_at", ""),
                })
        
        return {
            "notifications": notifications,
            "total": len(notifications)
        }
    except redis.ConnectionError as e:
        logger.warning("Redis not available, returning empty notifications", error=str(e))
        # Return empty list when Redis is unavailable
        return {
            "notifications": [],
            "total": 0,
            "redis_unavailable": True
        }
    except Exception as e:
        logger.error("Failed to get recent notifications", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get notifications")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": "connected",
                "slack": "configured" if settings.slack_bot_token else "not_configured"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Serve React app in production
if not settings.debug:
    app.mount("/", StaticFiles(directory="build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
