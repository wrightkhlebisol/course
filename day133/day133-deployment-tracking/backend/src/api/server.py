from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import json
import asyncio
from datetime import datetime
import uvicorn
import structlog
from typing import List
import os

# Import our modules
import sys
sys.path.append('/app/backend/src')

from deployment.detector import DeploymentDetector
from correlation.correlator import VersionCorrelator
from analysis.analyzer import ImpactAnalyzer

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(title="Deployment Tracking System", version="1.0.0")

# Global components
deployment_detector = None
version_correlator = None
impact_analyzer = None
connected_websockets: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    global deployment_detector, version_correlator, impact_analyzer
    
    logger.info("Starting Deployment Tracking System")
    
    # Initialize components
    config = {"sources": ["github", "docker", "kubernetes"]}
    deployment_detector = DeploymentDetector(config)
    version_correlator = VersionCorrelator(deployment_detector)
    impact_analyzer = ImpactAnalyzer(deployment_detector)
    
    # Start background tasks
    asyncio.create_task(deployment_detector.start_monitoring())
    asyncio.create_task(impact_analyzer.start_analysis())
    asyncio.create_task(websocket_broadcaster())

async def websocket_broadcaster():
    """Broadcast updates to connected websockets"""
    while True:
        try:
            if connected_websockets:
                # Prepare update data
                update_data = {
                    "timestamp": datetime.now().isoformat(),
                    "active_deployments": deployment_detector.get_active_deployments(),
                    "recent_deployments": deployment_detector.get_deployment_history()[-10:],
                    "impact_summary": impact_analyzer.get_impact_summary(),
                    "correlation_stats": version_correlator.get_correlation_stats()
                }
                
                # Send to all connected clients
                disconnected = []
                for websocket in connected_websockets:
                    try:
                        await websocket.send_text(json.dumps(update_data, default=str))
                    except:
                        disconnected.append(websocket)
                
                # Remove disconnected websockets
                for ws in disconnected:
                    connected_websockets.remove(ws)
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Websocket broadcaster error: {e}")
            await asyncio.sleep(5)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)

@app.get("/")
async def serve_dashboard():
    """Serve the main dashboard"""
    return FileResponse('/app/frontend/public/index.html')

@app.get("/api/deployments")
async def get_deployments():
    """Get all deployment data"""
    return {
        "active_deployments": deployment_detector.get_active_deployments(),
        "deployment_history": deployment_detector.get_deployment_history(),
        "total_count": len(deployment_detector.deployment_history)
    }

@app.get("/api/deployments/{deployment_id}/impact")
async def get_deployment_impact(deployment_id: str):
    """Get impact analysis for a specific deployment"""
    impact = next((r for r in impact_analyzer.impact_results if r.deployment_id == deployment_id), None)
    
    if impact:
        return {
            "deployment_id": impact.deployment_id,
            "service_name": impact.service_name,
            "version": impact.version,
            "before_metrics": impact.before_metrics,
            "after_metrics": impact.after_metrics,
            "impact_score": impact.impact_score,
            "significant_changes": impact.significant_changes,
            "analysis_timestamp": impact.analysis_timestamp.isoformat()
        }
    
    return {"error": "Impact analysis not found"}

@app.get("/api/impact/summary")
async def get_impact_summary():
    """Get overall impact analysis summary"""
    return impact_analyzer.get_impact_summary()

@app.get("/api/correlation/stats")
async def get_correlation_stats():
    """Get correlation statistics"""
    return version_correlator.get_correlation_stats()

@app.post("/api/logs/enrich")
async def enrich_log_entries(log_entries: List[dict]):
    """Enrich log entries with deployment context"""
    enriched = await version_correlator.batch_enrich_logs(log_entries)
    return {"enriched_logs": enriched, "count": len(enriched)}

# Mount static files for frontend
if os.path.exists('/app/frontend/build'):
    app.mount("/static", StaticFiles(directory="/app/frontend/build/static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
