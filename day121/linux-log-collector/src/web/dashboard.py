"""Real-time Web Dashboard"""
import asyncio
import json
import time
from typing import Dict, Any
import structlog
from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn


# Global stats storage (in production, use proper state management)
collector_stats = {
    'discovery': {},
    'monitor': {},
    'processor': {},
    'last_update': time.time()
}


def update_collector_stats(new_stats: Dict[str, Any]) -> None:
    """Update collector stats (called from collector components)"""
    collector_stats.update(new_stats)
    collector_stats['last_update'] = time.time()


app = FastAPI(title="Linux Log Collector Dashboard")

# Setup static files and templates
templates = Jinja2Templates(directory="src/web/templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Linux Log Collector",
        "stats": collector_stats
    })

@app.get("/api/stats")
async def get_stats():
    """Get current collector statistics"""
    return {
        "timestamp": time.time(),
        "stats": collector_stats,
        "uptime": time.time() - collector_stats.get('start_time', time.time())
    }

@app.post("/api/logs")
async def receive_logs(request: Request):
    """Receive logs from collector (for demo purposes)"""
    try:
        data = await request.json()
        
        # Update processor stats
        collector_stats['processor'] = {
            'batches_received': collector_stats.get('processor', {}).get('batches_received', 0) + 1,
            'logs_received': collector_stats.get('processor', {}).get('logs_received', 0) + len(data.get('logs', [])),
            'last_batch_time': time.time(),
            'last_batch_size': len(data.get('logs', []))
        }
        collector_stats['last_update'] = time.time()
        
        return {"status": "success", "processed": len(data.get('logs', []))}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    
    try:
        while True:
            try:
                await websocket.send_json({
                    "type": "stats_update",
                    "data": collector_stats,
                    "timestamp": time.time()
                })
                await asyncio.sleep(0.5)  # Update every 0.5 seconds for fast updates
            except Exception as e:
                # Client disconnected
                break
    except Exception as e:
        print(f"WebSocket connection error: {e}")


async def start_dashboard(config: Dict[str, Any]) -> None:
    """Start the web dashboard"""
    import threading
    port = config.get('web_port', 8000)
    
    # Set start time
    collector_stats['start_time'] = time.time()
    
    def run_server():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    
    # Run uvicorn in a thread to avoid blocking
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Wait a moment for server to start
    await asyncio.sleep(1)
    
    # Keep the async function running
    while True:
        await asyncio.sleep(1)
