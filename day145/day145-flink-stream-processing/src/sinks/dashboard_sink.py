"""
WebSocket sink for real-time dashboard updates
"""

import json
import asyncio
import websockets
import logging
from typing import Dict, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class DashboardSink:
    """Sends alerts and statistics to connected web dashboards"""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = False
        
    async def register_client(self, websocket):
        """Register new dashboard client"""
        self.connected_clients.add(websocket)
        logger.info(f"📱 Dashboard client connected. Total: {len(self.connected_clients)}")
        
    async def unregister_client(self, websocket):
        """Unregister dashboard client"""
        self.connected_clients.discard(websocket)
        logger.info(f"📱 Dashboard client disconnected. Total: {len(self.connected_clients)}")
        
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connected_clients:
            return
            
        message_json = json.dumps(message)
        
        # Send to all clients
        disconnected = set()
        for client in self.connected_clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
                
        # Clean up disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
            
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert to dashboard"""
        message = {
            'type': 'alert',
            'data': alert,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast(message)
        
    async def send_statistics(self, stats: Dict[str, Any]):
        """Send processing statistics to dashboard"""
        message = {
            'type': 'statistics',
            'data': stats,
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast(message)
        
    async def handle_client(self, websocket, path):
        """Handle individual client connection"""
        await self.register_client(websocket)
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'connected',
                'message': 'Connected to Flink Stream Processor'
            }))
            
            # Keep connection alive
            async for message in websocket:
                # Echo back for testing
                await websocket.send(json.dumps({
                    'type': 'echo',
                    'message': message
                }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
            
    async def start(self):
        """Start WebSocket server"""
        self.running = True
        self.server = await websockets.serve(
            self.handle_client,
            "0.0.0.0",
            self.port
        )
        logger.info(f"🚀 Dashboard WebSocket server started on port {self.port}")
        
    async def stop(self):
        """Stop WebSocket server"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("🛑 Dashboard sink stopped")
