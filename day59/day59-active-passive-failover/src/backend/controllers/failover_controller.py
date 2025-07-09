import asyncio
import time
import logging
from typing import Dict, List, Callable, Optional
from src.shared.models import ElectionMessage, FailoverEvent
from config.failover_config import config

logger = logging.getLogger(__name__)

class FailoverController:
    def __init__(self, node_id: str, on_failover_event: Callable[[FailoverEvent], None]):
        self.node_id = node_id
        self.on_failover_event = on_failover_event
        self.running = False
        
        # Election state
        self.election_in_progress = False
        self.election_votes: Dict[str, ElectionMessage] = {}
        self.election_start_time = 0
        
        # Priority calculation (lower ID = higher priority)
        self.priority = hash(node_id) % 1000
        
    async def start(self):
        """Start failover controller"""
        self.running = True
        
        # Start election monitor
        asyncio.create_task(self.monitor_elections())
        
        logger.info(f"Failover controller started for {self.node_id}")
    
    async def stop(self):
        """Stop failover controller"""
        self.running = False
        logger.info(f"Failover controller stopped for {self.node_id}")
    
    async def trigger_election(self):
        """Trigger leadership election"""
        if self.election_in_progress:
            logger.info("Election already in progress")
            return
        
        logger.info(f"Triggering election from {self.node_id}")
        
        self.election_in_progress = True
        self.election_start_time = time.time()
        self.election_votes = {}
        
        # Send election message
        election_msg = ElectionMessage(
            candidate_id=self.node_id,
            timestamp=time.time(),
            priority=self.priority
        )
        
        await self.broadcast_election_message(election_msg)
        
        # Wait for election to complete
        await asyncio.sleep(config.election_timeout)
        
        # Determine winner
        winner = await self.determine_election_winner()
        
        if winner:
            # Create failover event
            event = FailoverEvent(
                event_type="elected_primary",
                from_node=None,
                to_node=winner,
                timestamp=time.time(),
                duration=time.time() - self.election_start_time,
                metadata={'votes': len(self.election_votes)}
            )
            
            # Notify all nodes
            await self.broadcast_failover_event(event)
            
            # Notify local callback
            if self.on_failover_event:
                await self.on_failover_event(event)
        
        self.election_in_progress = False
    
    async def broadcast_election_message(self, message: ElectionMessage):
        """Broadcast election message to all nodes"""
        # In real implementation, this would use network sockets
        global_election_channel = self.get_global_election_channel()
        global_election_channel[self.node_id] = message.to_json()
    
    async def broadcast_failover_event(self, event: FailoverEvent):
        """Broadcast failover event to all nodes"""
        # In real implementation, this would use network sockets
        global_event_channel = self.get_global_event_channel()
        global_event_channel[f"event_{time.time()}"] = event.to_json()
    
    async def monitor_elections(self):
        """Monitor election messages"""
        while self.running:
            # Listen for election messages
            await self.listen_for_election_messages()
            
            # Listen for failover events
            await self.listen_for_failover_events()
            
            await asyncio.sleep(1)
    
    async def listen_for_election_messages(self):
        """Listen for election messages from other nodes"""
        global_election_channel = self.get_global_election_channel()
        
        for node_id, message_json in global_election_channel.items():
            if node_id != self.node_id:
                try:
                    message = ElectionMessage.from_json(message_json)
                    
                    # Participate in election
                    await self.participate_in_election(message)
                    
                except Exception as e:
                    logger.error(f"Error processing election message: {e}")
    
    async def listen_for_failover_events(self):
        """Listen for failover events"""
        global_event_channel = self.get_global_event_channel()
        
        for event_key, event_json in list(global_event_channel.items()):
            try:
                event = FailoverEvent.from_json(event_json)
                
                # Process event
                if self.on_failover_event:
                    await self.on_failover_event(event)
                
                # Remove processed event
                del global_event_channel[event_key]
                
            except Exception as e:
                logger.error(f"Error processing failover event: {e}")
    
    async def participate_in_election(self, message: ElectionMessage):
        """Participate in election by casting vote"""
        # Vote for candidate with highest priority (lowest ID)
        if message.candidate_id not in self.election_votes:
            self.election_votes[message.candidate_id] = message
            
            # Also vote for ourselves
            if self.node_id not in self.election_votes:
                self_message = ElectionMessage(
                    candidate_id=self.node_id,
                    timestamp=time.time(),
                    priority=self.priority
                )
                self.election_votes[self.node_id] = self_message
                await self.broadcast_election_message(self_message)
    
    async def determine_election_winner(self) -> Optional[str]:
        """Determine election winner based on votes"""
        if not self.election_votes:
            return None
        
        # Winner is candidate with highest priority (lowest priority number)
        winner = min(self.election_votes.keys(), 
                    key=lambda x: self.election_votes[x].priority)
        
        logger.info(f"Election winner: {winner}")
        return winner
    
    def get_global_election_channel(self) -> Dict[str, str]:
        """Get global election channel (simulated)"""
        if not hasattr(FailoverController, '_global_election_channel'):
            FailoverController._global_election_channel = {}
        return FailoverController._global_election_channel
    
    def get_global_event_channel(self) -> Dict[str, str]:
        """Get global event channel (simulated)"""
        if not hasattr(FailoverController, '_global_event_channel'):
            FailoverController._global_event_channel = {}
        return FailoverController._global_event_channel
