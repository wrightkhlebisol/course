from fastapi import FastAPI, Request, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import json
import asyncio
import logging
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import DatabaseAuditCollectorService

app = FastAPI(title="Database Audit Dashboard")
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Global service instance
audit_service = None

@app.on_event("startup")
async def startup():
    global audit_service
    audit_service = DatabaseAuditCollectorService()
    await audit_service.initialize()
    
    # Start background collection task
    asyncio.create_task(background_collection())

async def background_collection():
    """Background task to collect audit logs"""
    global audit_service
    while True:
        try:
            await audit_service.run_collection_cycle()
            await asyncio.sleep(30)
        except Exception as e:
            logging.error(f"Background collection error: {e}")
            await asyncio.sleep(5)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    """Get audit collection statistics"""
    if not audit_service:
        return {"error": "Service not initialized"}
    
    stats = {
        "total_logs": len(audit_service.audit_logs),
        "security_events": len(audit_service.security_events),
        "databases": {
            "postgresql": len([log for log in audit_service.audit_logs if log.get('database_type') == 'postgresql']),
            "mysql": len([log for log in audit_service.audit_logs if log.get('database_type') == 'mysql']),
            "mongodb": len([log for log in audit_service.audit_logs if log.get('database_type') == 'mongodb'])
        },
        "threat_types": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Count threat types
    for event in audit_service.security_events:
        threat_type = event.get('type', 'unknown')
        stats['threat_types'][threat_type] = stats['threat_types'].get(threat_type, 0) + 1
    
    return stats

@app.get("/api/logs")
async def get_recent_logs():
    """Get recent audit logs"""
    if not audit_service:
        return {"logs": []}
    
    # Return last 50 logs
    recent_logs = audit_service.audit_logs[-50:] if audit_service.audit_logs else []
    return {"logs": recent_logs}

@app.get("/api/threats")
async def get_security_threats():
    """Get recent security threats"""
    if not audit_service:
        return {"threats": []}
    
    return {"threats": audit_service.security_events}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    try:
        while True:
            # Send real-time stats
            stats = await get_stats()
            await websocket.send_text(json.dumps(stats))
            await asyncio.sleep(5)  # Update every 5 seconds
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
