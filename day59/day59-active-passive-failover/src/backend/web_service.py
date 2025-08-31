from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import logging
import time
import json
from typing import Dict, List
from src.backend.nodes.log_processor import LogProcessorNode, LogEntry
from src.shared.models import NodeState, NodeRole

logger = logging.getLogger(__name__)

class FailoverWebService:
    def __init__(self, node: LogProcessorNode):
        self.node = node
        self.app = FastAPI(title="Active-Passive Failover API", version="1.0.0")
        self.active_connections: List[WebSocket] = []
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                # Send initial status
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "data": self.node.get_health_status()
                }))
                
                # Keep connection alive and send periodic updates
                while True:
                    await asyncio.sleep(2)
                    
                    # Send periodic status updates
                    await websocket.send_text(json.dumps({
                        "type": "metrics",
                        "data": {
                            "throughput": self.node.metrics.get('logs_processed', 0),
                            "latency": 0.1,
                            "active_nodes": 3,
                            "failover_events": self.node.metrics.get('failover_events', 0),
                            "search_queries": self.node.metrics.get('search_queries', 0),
                            "uptime": self.node.metrics.get('uptime', 0)
                        }
                    }))
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for load balancer"""
            health_status = self.node.get_health_status()
            
            if health_status['healthy'] and health_status['role'] == 'primary':
                return JSONResponse(
                    status_code=200,
                    content=health_status
                )
            else:
                return JSONResponse(
                    status_code=503,
                    content=health_status
                )
        
        @self.app.get("/status")
        async def get_status():
            """Get detailed node status"""
            return self.node.get_health_status()
        
        @self.app.get("/nodes/status")
        async def get_nodes_status():
            """Get status of all nodes in the cluster"""
            # For demo purposes, return mock data for all nodes
            nodes = [
                {
                    'id': 'primary',
                    'status': 'primary',
                    'healthy': True,
                    'port': 8001
                },
                {
                    'id': 'standby-1', 
                    'status': 'standby',
                    'healthy': True,
                    'port': 8002
                },
                {
                    'id': 'standby-2',
                    'status': 'standby', 
                    'healthy': True,
                    'port': 8003
                }
            ]
            
            return {
                'nodes': nodes,
                'system_health': 'healthy',
                'timestamp': time.time()
            }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get system metrics"""
            return {
                'throughput': self.node.metrics.get('logs_processed', 0),
                'latency': 0.1,  # Mock latency
                'active_nodes': 3,  # Mock active nodes count
                'failover_events': self.node.metrics.get('failover_events', 0),
                'search_queries': self.node.metrics.get('search_queries', 0),
                'uptime': self.node.metrics.get('uptime', 0)
            }
        
        @self.app.get("/failover/events")
        async def get_failover_events():
            """Get failover events history"""
            # Mock failover events for demo
            events = [
                {
                    'id': 1,
                    'type': 'election_started',
                    'timestamp': time.time() - 3600,
                    'node_id': 'primary',
                    'details': 'Leadership election initiated'
                }
            ]
            
            return {
                'events': events,
                'total': len(events)
            }
        
        @self.app.post("/nodes/{node_id}/trigger-failover")
        async def trigger_node_failover(node_id: str):
            """Trigger failover for a specific node"""
            if self.node.role == NodeRole.PRIMARY and node_id == self.node.node_id:
                # Simulate primary failure
                await self.node.stop()
                return {"status": "failover_triggered", "node_id": node_id}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot trigger failover for node {node_id}"
                )
        
        @self.app.post("/logs")
        async def submit_log(log_data: Dict):
            """Submit log entry for processing"""
            if self.node.role != NodeRole.PRIMARY:
                raise HTTPException(
                    status_code=503,
                    detail="Node is not primary"
                )
            
            log_entry = LogEntry(
                timestamp=log_data.get('timestamp', time.time()),
                level=log_data.get('level', 'INFO'),
                message=log_data.get('message', ''),
                source=log_data.get('source', 'unknown'),
                metadata=log_data.get('metadata', {})
            )
            
            self.node.log_buffer.append(log_entry)
            
            return {"status": "accepted", "log_id": len(self.node.log_buffer)}
        
        @self.app.get("/logs/search")
        async def search_logs(query: str, limit: int = 10):
            """Search logs"""
            if self.node.role != NodeRole.PRIMARY:
                raise HTTPException(
                    status_code=503,
                    detail="Node is not primary"
                )
            
            # Simple search implementation
            results = []
            for timestamp, log_entry in self.node.search_index.items():
                if query.lower() in log_entry.message.lower():
                    results.append({
                        'timestamp': timestamp,
                        'level': log_entry.level,
                        'message': log_entry.message,
                        'source': log_entry.source
                    })
                    
                    if len(results) >= limit:
                        break
            
            self.node.metrics['search_queries'] += 1
            return {"results": results, "total": len(results)}
        
        @self.app.post("/admin/trigger-failover")
        async def trigger_failover():
            """Trigger failover for testing"""
            if self.node.role == NodeRole.PRIMARY:
                # Simulate primary failure
                await self.node.stop()
                return {"status": "failover_triggered"}
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Node is not primary"
                )
    
    async def start_server(self):
        """Start the web server"""
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.node.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
