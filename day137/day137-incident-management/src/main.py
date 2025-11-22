"""
Day 137: PagerDuty/OpsGenie Integration System
Main application entry point with FastAPI server
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from core.config import get_settings
from core.alert_router import AlertRouter
from integrations.incident_manager import IncidentManager
from webhooks.webhook_handler import WebhookHandler
from monitoring.health_monitor import HealthMonitor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()

# Global instances
alert_router = None
incident_manager = None
webhook_handler = None
health_monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and cleanup application lifecycle"""
    global alert_router, incident_manager, webhook_handler, health_monitor
    
    logger.info("🚀 Starting PagerDuty/OpsGenie Integration System")
    
    # Initialize core components
    settings = get_settings()
    
    # Initialize incident manager with provider configurations
    incident_manager = IncidentManager(
        pagerduty_api_key=settings.pagerduty_api_key,
        opsgenie_api_key=settings.opsgenie_api_key
    )
    await incident_manager.initialize()
    
    # Initialize alert router with escalation policies
    alert_router = AlertRouter(incident_manager)
    await alert_router.load_escalation_policies()
    
    # Initialize webhook handler for bidirectional communication
    webhook_handler = WebhookHandler(incident_manager, alert_router)
    
    # Initialize health monitoring
    health_monitor = HealthMonitor(incident_manager)
    await health_monitor.start_monitoring()
    
    logger.info("✅ All systems initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down systems...")
    if health_monitor:
        await health_monitor.stop_monitoring()
    if incident_manager:
        await incident_manager.cleanup()

# Create FastAPI application
app = FastAPI(
    title="Incident Management Integration System",
    description="PagerDuty/OpsGenie integration for distributed log processing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.post("/api/v1/alerts")
async def create_alert(alert_data: dict, request: Request):
    """Create new alert and route to appropriate incident management system"""
    try:
        result = await alert_router.process_alert(alert_data)
        
        # Record metrics
        if health_monitor:
            health_monitor.record_alert_processed()
            # Check if any incidents were successfully created
            if result.get("success") and any(r.get("success") for r in result.get("routing_results", [])):
                health_monitor.record_incident_created()
        
        logger.info("Alert processed successfully", 
                   alert_id=result.get("alert_id"), 
                   provider=result.get("provider"))
        return result
    except Exception as e:
        logger.error("Failed to process alert", error=str(e))
        # Still record the alert attempt
        if health_monitor:
            health_monitor.record_alert_processed()
        raise

@app.get("/api/v1/incidents")
async def get_incidents():
    """Get current incidents from all providers"""
    return await incident_manager.get_all_incidents()

@app.get("/api/v1/health")
async def get_health():
    """Get system health status"""
    return await health_monitor.get_health_status()

@app.get("/api/v1/metrics")
async def get_metrics():
    """Get integration metrics"""
    return await health_monitor.get_metrics()

@app.post("/api/v1/webhooks/pagerduty")
async def pagerduty_webhook(request: Request):
    """Handle PagerDuty webhooks"""
    body = await request.body()
    headers = dict(request.headers)
    return await webhook_handler.handle_pagerduty_webhook(body, headers)

@app.post("/api/v1/webhooks/opsgenie")
async def opsgenie_webhook(request: Request):
    """Handle OpsGenie webhooks"""
    body = await request.body()
    headers = dict(request.headers)
    return await webhook_handler.handle_opsgenie_webhook(body, headers)

# Serve React frontend
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve React frontend for all routes"""
    return HTMLResponse(open("frontend/build/index.html").read())

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None
    )
