import asyncio
import time
import logging
from typing import Dict, Callable, Optional
from src.shared.models import HeartbeatMessage, NodeState, NodeRole
from config.failover_config import config

logger = logging.getLogger(__name__)

class HeartbeatManager:
    def __init__(self, node_id: str, on_heartbeat_lost: Callable[[str], None]):
        self.node_id = node_id
        self.on_heartbeat_lost = on_heartbeat_lost
        self.running = False
        
        # Heartbeat tracking
        self.last_heartbeats: Dict[str, float] = {}
        self.heartbeat_tasks = []
        
        # Mock network communication
        self.heartbeat_channel = {}
        
    async def start(self):
        """Start heartbeat manager"""
        self.running = True
        
        # Start heartbeat sender
        self.heartbeat_tasks.append(
            asyncio.create_task(self.send_heartbeats())
        )
        
        # Start heartbeat monitor
        self.heartbeat_tasks.append(
            asyncio.create_task(self.monitor_heartbeats())
        )
        
        logger.info(f"Heartbeat manager started for {self.node_id}")
    
    async def stop(self):
        """Stop heartbeat manager"""
        self.running = False
        
        # Cancel all tasks
        for task in self.heartbeat_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.heartbeat_tasks, return_exceptions=True)
        
        logger.info(f"Heartbeat manager stopped for {self.node_id}")
    
    async def send_heartbeats(self):
        """Send periodic heartbeats"""
        while self.running:
            heartbeat = HeartbeatMessage(
                node_id=self.node_id,
                timestamp=time.time(),
                state=NodeState.PRIMARY,  # This would be dynamic
                role=NodeRole.PRIMARY,    # This would be dynamic
                data={'metrics': {'processed': 100}}
            )
            
            # Broadcast to all nodes (simulated)
            await self.broadcast_heartbeat(heartbeat)
            
            await asyncio.sleep(config.heartbeat_interval)
    
    async def broadcast_heartbeat(self, heartbeat: HeartbeatMessage):
        """Broadcast heartbeat to all nodes"""
        # In real implementation, this would use network sockets
        # For demo, we use a shared dictionary
        global_heartbeat_channel = self.get_global_channel()
        global_heartbeat_channel[self.node_id] = heartbeat.to_json()
    
    async def monitor_heartbeats(self):
        """Monitor heartbeats from other nodes"""
        while self.running:
            current_time = time.time()
            
            # Check for missing heartbeats
            for node_id, last_heartbeat in self.last_heartbeats.items():
                if current_time - last_heartbeat > config.heartbeat_timeout:
                    logger.warning(f"Lost heartbeat from {node_id}")
                    
                    # Remove from tracking
                    del self.last_heartbeats[node_id]
                    
                    # Notify callback
                    if self.on_heartbeat_lost:
                        await self.on_heartbeat_lost(node_id)
            
            # Listen for new heartbeats
            await self.listen_for_heartbeats()
            
            await asyncio.sleep(1)
    
    async def listen_for_heartbeats(self):
        """Listen for heartbeats from other nodes"""
        # In real implementation, this would use network sockets
        global_heartbeat_channel = self.get_global_channel()
        
        for node_id, heartbeat_json in global_heartbeat_channel.items():
            if node_id != self.node_id:
                try:
                    heartbeat = HeartbeatMessage.from_json(heartbeat_json)
                    self.last_heartbeats[node_id] = heartbeat.timestamp
                except json.JSONDecodeError:
                    logger.error(f"Invalid heartbeat from {node_id}")
    
    def get_global_channel(self) -> Dict[str, str]:
        """Get global heartbeat channel (simulated)"""
        if not hasattr(HeartbeatManager, '_global_channel'):
            HeartbeatManager._global_channel = {}
        return HeartbeatManager._global_channel
