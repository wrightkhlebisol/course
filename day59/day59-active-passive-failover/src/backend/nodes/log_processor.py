import asyncio
import json
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from src.shared.models import NodeState, NodeRole, HeartbeatMessage, FailoverEvent
from src.backend.utils.state_manager import StateManager
from src.backend.utils.heartbeat_manager import HeartbeatManager
from src.backend.controllers.failover_controller import FailoverController

logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    timestamp: float
    level: str
    message: str
    source: str
    metadata: Dict = field(default_factory=dict)

class LogProcessorNode:
    def __init__(self, node_id: str, port: int, is_primary: bool = False):
        self.node_id = node_id
        self.port = port
        self.is_primary = is_primary
        self.state = NodeState.INACTIVE
        self.role = NodeRole.PRIMARY if is_primary else NodeRole.STANDBY
        
        # Components
        self.state_manager = StateManager(node_id)
        self.heartbeat_manager = HeartbeatManager(node_id, self.on_heartbeat_lost)
        self.failover_controller = FailoverController(node_id, self.on_failover_event)
        
        # Application state
        self.log_buffer: List[LogEntry] = []
        self.processed_count = 0
        self.search_index = {}
        self.running = False
        
        # Health metrics
        self.metrics = {
            'logs_processed': 0,
            'search_queries': 0,
            'failover_events': 0,
            'uptime': 0
        }
        
    async def start(self):
        """Start the log processor node"""
        logger.info(f"Starting node {self.node_id} on port {self.port}")
        
        # Initialize state
        await self.state_manager.initialize()
        
        # Start heartbeat
        await self.heartbeat_manager.start()
        
        # Start failover controller
        await self.failover_controller.start()
        
        # Set initial state
        if self.is_primary:
            await self.become_primary()
        else:
            await self.become_standby()
            
        self.running = True
        
        # Start background tasks
        asyncio.create_task(self.process_logs())
        asyncio.create_task(self.sync_state())
        asyncio.create_task(self.update_metrics())
        
        logger.info(f"Node {self.node_id} started successfully")
    
    async def stop(self):
        """Stop the log processor node"""
        logger.info(f"Stopping node {self.node_id}")
        
        self.running = False
        
        # Stop components
        await self.heartbeat_manager.stop()
        await self.failover_controller.stop()
        await self.state_manager.cleanup()
        
        logger.info(f"Node {self.node_id} stopped")
    
    async def become_primary(self):
        """Transition to primary role"""
        logger.info(f"Node {self.node_id} becoming primary")
        
        self.role = NodeRole.PRIMARY
        self.state = NodeState.PRIMARY
        
        # Load state from shared storage
        await self.load_state()
        
        # Start accepting requests
        await self.start_request_handler()
        
        logger.info(f"Node {self.node_id} is now primary")
    
    async def become_standby(self):
        """Transition to standby role"""
        logger.info(f"Node {self.node_id} becoming standby")
        
        self.role = NodeRole.STANDBY
        self.state = NodeState.STANDBY
        
        # Stop accepting requests
        await self.stop_request_handler()
        
        # Start monitoring primary
        await self.monitor_primary()
        
        logger.info(f"Node {self.node_id} is now standby")
    
    async def process_logs(self):
        """Process logs from buffer"""
        while self.running:
            if self.role == NodeRole.PRIMARY and self.log_buffer:
                # Process logs in batch
                batch = self.log_buffer[:100]
                self.log_buffer = self.log_buffer[100:]
                
                for log_entry in batch:
                    await self.process_single_log(log_entry)
                    self.processed_count += 1
                    self.metrics['logs_processed'] += 1
                
                # Save state periodically
                if self.processed_count % 100 == 0:
                    await self.save_state()
            
            await asyncio.sleep(0.1)
    
    async def process_single_log(self, log_entry: LogEntry):
        """Process a single log entry"""
        # Add to search index
        self.search_index[log_entry.timestamp] = log_entry
        
        # Simulate processing time
        await asyncio.sleep(0.001)
    
    async def save_state(self):
        """Save current state to shared storage"""
        state_data = {
            'processed_count': self.processed_count,
            'search_index_size': len(self.search_index),
            'log_buffer_size': len(self.log_buffer),
            'timestamp': time.time()
        }
        
        await self.state_manager.save_state(state_data)
    
    async def load_state(self):
        """Load state from shared storage"""
        state_data = await self.state_manager.load_state()
        
        if state_data:
            self.processed_count = state_data.get('processed_count', 0)
            logger.info(f"Loaded state: processed_count={self.processed_count}")
    
    async def sync_state(self):
        """Synchronize state with shared storage"""
        while self.running:
            if self.role == NodeRole.PRIMARY:
                await self.save_state()
            
            await asyncio.sleep(5)  # Sync every 5 seconds
    
    async def update_metrics(self):
        """Update node metrics"""
        start_time = time.time()
        
        while self.running:
            self.metrics['uptime'] = time.time() - start_time
            await asyncio.sleep(1)
    
    async def on_heartbeat_lost(self, lost_node_id: str):
        """Handle heartbeat loss from primary"""
        if self.role == NodeRole.STANDBY:
            logger.warning(f"Lost heartbeat from {lost_node_id}")
            await self.failover_controller.trigger_election()
    
    async def on_failover_event(self, event: FailoverEvent):
        """Handle failover events"""
        logger.info(f"Failover event: {event.event_type}")
        
        if event.event_type == "elected_primary" and event.to_node == self.node_id:
            await self.become_primary()
        elif event.event_type == "new_primary" and event.to_node != self.node_id:
            await self.become_standby()
        
        self.metrics['failover_events'] += 1
    
    async def start_request_handler(self):
        """Start handling external requests"""
        # This would start the FastAPI server
        logger.info("Starting request handler")
    
    async def stop_request_handler(self):
        """Stop handling external requests"""
        # This would stop the FastAPI server
        logger.info("Stopping request handler")
    
    async def monitor_primary(self):
        """Monitor primary node health"""
        # This would monitor the primary node
        logger.info("Monitoring primary node")
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        return {
            'node_id': self.node_id,
            'state': self.state.value,
            'role': self.role.value,
            'metrics': self.metrics,
            'healthy': self.running and self.state != NodeState.FAILED
        }
