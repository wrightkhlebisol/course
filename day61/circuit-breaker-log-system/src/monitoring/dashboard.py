"""
Dashboard and monitoring functionality for circuit breaker system
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import collections.abc

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from src.circuit_breaker.core import registry
from src.services.log_processor import LogProcessorService

logger = logging.getLogger(__name__)

def convert_datetimes(obj):
    """Recursively convert datetime objects to ISO strings in a dict/list structure."""
    if isinstance(obj, dict):
        return {k: convert_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

class CircuitBreakerMonitor:
    """Real-time monitoring for circuit breakers"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_processor = LogProcessorService()
        self.metrics_history = []
        self.max_history_size = 1000
    
    async def connect(self, websocket: WebSocket):
        """Connect websocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect websocket client"""
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics to all connected clients"""
        if not self.active_connections:
            return
        # Convert all datetime objects to strings
        safe_metrics = convert_datetimes(metrics)
        message = json.dumps(safe_metrics)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive metrics"""
        circuit_stats = registry.get_all_stats()
        processing_stats = self.log_processor.get_processing_stats()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'circuit_breakers': circuit_stats,
            'processing': processing_stats,
            'system': {
                'active_connections': len(self.active_connections),
                'metrics_history_size': len(self.metrics_history)
            }
        }
        
        # Add to history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
        
        return metrics
    
    def get_metrics_history(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """Get metrics history for specified time period"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        filtered_history = []
        for metric in self.metrics_history:
            metric_time = datetime.fromisoformat(metric['timestamp'])
            if metric_time >= cutoff_time:
                filtered_history.append(metric)
        
        return filtered_history

# Create FastAPI app
app = FastAPI(title="Circuit Breaker Monitor", version="1.0.0")
templates = Jinja2Templates(directory="templates")
monitor = CircuitBreakerMonitor()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/metrics")
async def get_metrics():
    """Get current metrics"""
    return monitor.collect_metrics()

@app.get("/api/metrics/history")
async def get_metrics_history(minutes: int = 10):
    """Get metrics history"""
    return monitor.get_metrics_history(minutes)

@app.post("/api/simulate/failures")
async def simulate_failures(duration: int = 30):
    """Simulate failure scenarios"""
    asyncio.create_task(run_failure_simulation(duration))
    return {"status": "started", "duration": duration}

@app.post("/api/process/logs")
async def process_test_logs(count: int = 10):
    """Process test logs for demonstration"""
    results = []
    for i in range(count):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': ['INFO', 'WARN', 'ERROR'][i % 3],
            'message': f'Test log message {i+1}',
            'service': f'test-service-{(i % 3) + 1}',
            'user_id': f'user_{i % 100}'
        }
        result = monitor.log_processor.process_log(log_data)
        results.append(result)
    
    return {"processed": len(results), "results": results}

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await monitor.connect(websocket)
    try:
        while True:
            await asyncio.sleep(2)  # Update every 2 seconds
            metrics = monitor.collect_metrics()
            await monitor.broadcast_metrics(metrics)
    except WebSocketDisconnect:
        monitor.disconnect(websocket)

async def run_failure_simulation(duration: int):
    """Run failure simulation in background"""
    monitor.log_processor.simulate_failures(duration)

# Background task for regular metrics collection
@app.on_event("startup")
async def startup_event():
    """Start background metrics collection"""
    asyncio.create_task(metrics_collector())

async def metrics_collector():
    """Background task to collect metrics"""
    while True:
        try:
            metrics = monitor.collect_metrics()
            await monitor.broadcast_metrics(metrics)
            await asyncio.sleep(5)  # Collect every 5 seconds
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
