"""
Web API and dashboard server
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

app = FastAPI(title="Flink Stream Processing Dashboard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections = []

# Statistics storage
latest_stats = {
    'processed_count': 0,
    'alert_count': 0,
    'throughput_per_second': 0
}

recent_alerts = []


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve dashboard HTML"""
    html_path = Path(__file__).parent.parent.parent / "web" / "templates" / "dashboard.html"
    return FileResponse(html_path)


@app.get("/api/stats")
async def get_stats():
    """Get current processing statistics"""
    return latest_stats


@app.get("/api/alerts")
async def get_alerts():
    """Get recent alerts"""
    return {"alerts": recent_alerts[-50:]}  # Last 50 alerts


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"📱 WebSocket client connected. Total: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"📱 WebSocket client disconnected. Total: {len(active_connections)}")


async def broadcast_update(data: dict):
    """Broadcast update to all connected clients"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


def update_stats(stats: dict):
    """Update statistics"""
    global latest_stats
    latest_stats = stats


def add_alert(alert: dict):
    """Add new alert"""
    recent_alerts.append(alert)
    if len(recent_alerts) > 100:
        recent_alerts.pop(0)
