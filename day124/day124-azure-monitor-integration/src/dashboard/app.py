import asyncio
import json
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from azure_monitor.connector import AzureMonitorConnector
from azure_monitor.processor import AzureLogProcessor
from config.azure_config import DEMO_CONFIG

app = FastAPI(title="Azure Monitor Integration Dashboard")

# Get project root directory (parent of src)
from pathlib import Path
import json
# __file__ is src/dashboard/app.py, so parent.parent.parent gets project root
project_root = Path(__file__).parent.parent.parent
web_static_dir = str(project_root / "web" / "static")
web_templates_dir = str(project_root / "web" / "templates")

app.mount("/static", StaticFiles(directory=web_static_dir), name="static")
templates = Jinja2Templates(directory=web_templates_dir)

# Add json filter for templates
def tojsonfilter(value):
    """Convert value to JSON string for templates"""
    return json.dumps(value)

templates.env.filters['tojsonfilter'] = tojsonfilter

# Global instances
azure_connector = AzureMonitorConnector(DEMO_CONFIG)
log_processor = AzureLogProcessor()
connected_websockets = set()

@app.on_event("startup")
async def startup_event():
    """Initialize Azure connector on startup"""
    await azure_connector.connect()
    # Start background log collection
    asyncio.create_task(collect_logs_background())
    # Start periodic stats updates
    asyncio.create_task(send_periodic_stats_updates())

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    stats = log_processor.get_statistics()
    insights = log_processor.get_insights_summary()
    health = await azure_connector.get_health_status()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "insights": insights,
        "health": health,
        "title": "Azure Monitor Integration Dashboard"
    })

@app.get("/api/stats")
async def get_stats():
    """Get current statistics"""
    return log_processor.get_statistics()

@app.get("/api/insights")  
async def get_insights():
    """Get insights summary"""
    return log_processor.get_insights_summary()

@app.get("/api/health")
async def get_health():
    """Get connector health status"""
    return await azure_connector.get_health_status()

@app.get("/api/recent-logs")
async def get_recent_logs(limit: int = 50):
    """Get recent log entries"""
    return log_processor.get_recent_logs(limit)

@app.get("/api/workspaces")
async def get_workspaces():
    """Get discovered workspaces"""
    return await azure_connector.discover_workspaces()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    connected_websockets.add(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        pass
    finally:
        connected_websockets.discard(websocket)

async def collect_logs_background():
    """Background task to collect logs from Azure Monitor"""
    while True:
        try:
            workspaces = await azure_connector.discover_workspaces()
            
            for workspace in workspaces:
                workspace_id = workspace['id']
                
                async for log_entry in azure_connector.query_logs(workspace_id):
                    processed_entry = await log_processor.process_log_entry(log_entry)
                    
                    # Send real-time update to connected clients
                    if connected_websockets:
                        message = {
                            'type': 'new_log',
                            'data': processed_entry,
                            'stats': log_processor.get_statistics()
                        }
                        
                        # Send to all connected clients
                        disconnected = set()
                        for ws in connected_websockets:
                            try:
                                await ws.send_text(json.dumps(message))
                            except:
                                disconnected.add(ws)
                        
                        # Remove disconnected clients
                        connected_websockets -= disconnected
            
            # Wait before next collection cycle
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Background collection error: {e}")
            await asyncio.sleep(60)  # Wait longer on error

async def send_periodic_stats_updates():
    """Periodically send stats updates to connected clients for real-time metrics"""
    while True:
        try:
            await asyncio.sleep(5)  # Send stats every 5 seconds
            
            if connected_websockets:
                message = {
                    'type': 'stats_update',
                    'stats': log_processor.get_statistics()
                }
                
                # Send to all connected clients
                disconnected = set()
                for ws in connected_websockets:
                    try:
                        await ws.send_text(json.dumps(message))
                    except:
                        disconnected.add(ws)
                
                # Remove disconnected clients
                connected_websockets -= disconnected
                
        except Exception as e:
            print(f"Periodic stats update error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
