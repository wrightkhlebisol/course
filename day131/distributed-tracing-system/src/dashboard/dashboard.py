import json
import asyncio
from typing import List, Dict
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import structlog
from src.tracing.collector import get_trace_collector
from config.config import config

app = FastAPI(title="Distributed Tracing Dashboard", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

logger = structlog.get_logger()

# WebSocket connections
active_connections: List[WebSocket] = []

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/traces")
async def get_traces():
    """Get recent traces API"""
    try:
        trace_collector = await get_trace_collector()
        traces = await trace_collector.get_recent_traces(limit=100)
        return {"traces": traces}
    except Exception as e:
        logger.error("Failed to get traces", error=str(e))
        return {"traces": [], "error": str(e)}

@app.get("/api/trace/{trace_id}")
async def get_trace_details(trace_id: str):
    """Get detailed trace information"""
    try:
        trace_collector = await get_trace_collector()
        spans = await trace_collector.get_trace(trace_id)
        return {"trace_id": trace_id, "spans": spans}
    except Exception as e:
        logger.error("Failed to get trace details", trace_id=trace_id, error=str(e))
        return {"trace_id": trace_id, "spans": [], "error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            trace_collector = await get_trace_collector()
            traces = await trace_collector.get_recent_traces(limit=10)
            
            await websocket.send_json({
                "type": "traces_update",
                "data": traces
            })
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        if websocket in active_connections:
            active_connections.remove(websocket)

async def broadcast_trace_update(trace_data: Dict):
    """Broadcast trace update to all connected clients"""
    if active_connections:
        message = {
            "type": "new_trace",
            "data": trace_data
        }
        
        disconnected = []
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            active_connections.remove(connection)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.dashboard.dashboard:app",
        host=config.dashboard_host,
        port=config.dashboard_port,
        reload=False
    )
