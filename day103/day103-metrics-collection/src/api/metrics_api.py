from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import structlog
from datetime import datetime
from typing import List, Dict
from src.aggregators.metrics_aggregator import MetricsAggregator
from src.alerts.alert_manager import AlertManager
from config.metrics_config import MetricsConfig

logger = structlog.get_logger(__name__)

class MetricsAPI:
    def __init__(self, aggregator: MetricsAggregator, alert_manager: AlertManager, config: MetricsConfig):
        self.aggregator = aggregator
        self.alert_manager = alert_manager
        self.config = config
        self.app = FastAPI(title="Metrics Collection API", version="1.0.0")
        self.websocket_connections = []
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/metrics/current")
        async def get_current_metrics():
            """Get current metrics snapshot"""
            return await self.aggregator.get_current_snapshot()
        
        @self.app.get("/metrics/{metric_name}")
        async def get_metric_history(metric_name: str, minutes: int = 5):
            """Get historical data for a specific metric"""
            metrics = await self.aggregator.get_recent_metrics(metric_name, minutes)
            return {
                "metric_name": metric_name,
                "time_window_minutes": minutes,
                "data_points": len(metrics),
                "metrics": [
                    {
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags
                    } for m in metrics
                ]
            }
        
        @self.app.get("/alerts")
        async def get_alerts():
            """Get active alerts"""
            alerts = await self.alert_manager.get_active_alerts()
            return {
                "active_alerts": len(alerts),
                "alerts": [
                    {
                        "id": alert.id,
                        "metric_name": alert.metric_name,
                        "level": alert.level.value,
                        "message": alert.message,
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "timestamp": alert.timestamp.isoformat()
                    } for alert in alerts
                ]
            }
        
        @self.app.post("/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve an alert"""
            await self.alert_manager.resolve_alert(alert_id)
            return {"status": "resolved", "alert_id": alert_id}
        
        @self.app.websocket("/ws/metrics")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time metrics"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Send current metrics every 2 seconds
                    snapshot = await self.aggregator.get_current_snapshot()
                    alerts = await self.alert_manager.get_active_alerts()
                    
                    data = {
                        "type": "metrics_update",
                        "timestamp": datetime.now().isoformat(),
                        "metrics": snapshot,
                        "alerts": [
                            {
                                "id": alert.id,
                                "level": alert.level.value,
                                "message": alert.message,
                                "current_value": alert.current_value
                            } for alert in alerts
                        ]
                    }
                    
                    await websocket.send_text(json.dumps(data))
                    await asyncio.sleep(2)
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def broadcast_alert(self, alert):
        """Broadcast alert to all WebSocket connections"""
        if not self.websocket_connections:
            return
        
        data = {
            "type": "alert",
            "alert": {
                "id": alert.id,
                "level": alert.level.value,
                "message": alert.message,
                "current_value": alert.current_value,
                "timestamp": alert.timestamp.isoformat()
            }
        }
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(data))
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)
