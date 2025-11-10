from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import asyncio
import json
from typing import Set, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LogAPIServer:
    """FastAPI server for log collection dashboard"""
    
    def __init__(self, multiplexer, docker_collector, k8s_collector, enricher):
        self.app = FastAPI(title="Container Log Collector")
        self.multiplexer = multiplexer
        self.docker_collector = docker_collector
        self.k8s_collector = k8s_collector
        self.enricher = enricher
        self.websocket_clients: Set[WebSocket] = set()
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Serve dashboard HTML"""
            # Get the base directory (parent of src)
            base_dir = Path(__file__).parent.parent.parent
            dashboard_path = base_dir / 'web' / 'templates' / 'dashboard.html'
            html_content = dashboard_path.read_text()
            return HTMLResponse(content=html_content)
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get collection statistics"""
            docker_containers = []
            if self.docker_collector:
                # discover_containers() now works even without client (uses CLI fallback)
                docker_containers = self.docker_collector.discover_containers()
            
            k8s_pods = []
            if self.k8s_collector and self.k8s_collector.core_v1:
                k8s_pods = self.k8s_collector.discover_pods()
            
            return JSONResponse({
                'docker': {
                    'enabled': self.docker_collector is not None,
                    'containers': len(docker_containers),
                    'active_streams': len(self.docker_collector.active_streams) if self.docker_collector else 0
                },
                'kubernetes': {
                    'enabled': self.k8s_collector is not None,
                    'pods': len(k8s_pods),
                    'active_streams': len(self.k8s_collector.active_streams) if self.k8s_collector else 0
                },
                'multiplexer': self.multiplexer.get_stats(),
                'websocket_clients': len(self.websocket_clients)
            })
        
        @self.app.get("/api/containers")
        async def list_containers():
            """List discovered containers and pods"""
            containers = []
            if self.docker_collector:
                # discover_containers() now works even without client (uses CLI fallback)
                containers.extend(self.docker_collector.discover_containers())
            
            if self.k8s_collector and self.k8s_collector.core_v1:
                containers.extend(self.k8s_collector.discover_pods())
            
            return JSONResponse({'containers': containers})
        
        @self.app.get("/api/recent-logs")
        async def recent_logs():
            """Get recent log entries"""
            logs = self.multiplexer.get_recent_logs(50)
            return JSONResponse({'logs': logs})
        
        @self.app.post("/api/test/generate-logs")
        async def generate_test_logs():
            """Generate test logs for demonstration"""
            import asyncio
            from datetime import datetime
            import random
            
            async def generate():
                levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
                messages = [
                    'Application started successfully',
                    'Processing user request',
                    'Database query executed',
                    'Cache hit for key',
                    'Warning: High memory usage detected',
                    'Error: Failed to connect to service',
                    'Debug: Tracing function execution',
                    'Info: Service health check passed'
                ]
                for i in range(20):
                    level = random.choice(levels)
                    message = random.choice(messages)
                    test_log = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'message': f'[{level}] {message} - Request ID: {random.randint(1000, 9999)}',
                        'source': 'test',
                        'container_name': 'test-generator',
                        'level': level
                    }
                    enriched = self.enricher.enrich(test_log)
                    await self.multiplexer.add_log(enriched)
                    await asyncio.sleep(0.3)
            
            # Run in background
            asyncio.create_task(generate())
            return JSONResponse({'status': 'generating', 'count': 20})
        
        @self.app.websocket("/ws/logs")
        async def websocket_logs(websocket: WebSocket):
            """WebSocket endpoint for real-time logs"""
            await websocket.accept()
            self.websocket_clients.add(websocket)
            logger.info(f"WebSocket client connected. Total: {len(self.websocket_clients)}")
            
            try:
                # Send recent logs first
                recent = self.multiplexer.get_recent_logs(20)
                for log in recent:
                    await websocket.send_json(log)
                
                # Keep connection alive and handle client messages (non-blocking)
                while True:
                    try:
                        # Wait for client messages with timeout (ping/filter updates)
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                        # Echo back or handle filter updates
                        await websocket.send_json({'status': 'connected'})
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send_json({'status': 'ping'})
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                self.websocket_clients.discard(websocket)
        
        async def broadcast_to_websockets(log_entry: Dict):
            """Broadcast log to all WebSocket clients"""
            disconnected = set()
            for client in self.websocket_clients:
                try:
                    await client.send_json(log_entry)
                except Exception:
                    disconnected.add(client)
            
            # Clean up disconnected clients
            for client in disconnected:
                self.websocket_clients.discard(client)
        
        # Register websocket broadcaster as consumer
        self.multiplexer.add_consumer(broadcast_to_websockets)
