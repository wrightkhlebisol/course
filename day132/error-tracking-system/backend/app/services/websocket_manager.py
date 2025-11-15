"""WebSocket manager for real-time error tracking updates"""

from typing import List, Dict
from fastapi import WebSocket
import json
import asyncio

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_error_update(self, data: Dict):
        """Send error update to all connected clients"""
        if self.active_connections:
            message = json.dumps({
                "type": "error_update",
                "data": data
            })
            
            # Send to all connections, remove failed ones
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection)
    
    async def send_group_update(self, data: Dict):
        """Send group update to all connected clients"""
        if self.active_connections:
            message = json.dumps({
                "type": "group_update", 
                "data": data
            })
            
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)
            
            for connection in disconnected:
                self.disconnect(connection)

# Global instance
websocket_manager = WebSocketManager()
