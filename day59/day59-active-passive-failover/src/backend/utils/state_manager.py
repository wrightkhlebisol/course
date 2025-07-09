import redis
import json
import asyncio
from typing import Dict, Any, Optional
from config.failover_config import config

class StateManager:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.redis_client = None
        self.state_key = f"node_state:{node_id}"
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True
        )
        
        # Test connection
        try:
            self.redis_client.ping()
        except redis.ConnectionError:
            # Fallback to in-memory storage for demo
            self.redis_client = InMemoryRedis()
    
    async def save_state(self, state_data: Dict[str, Any]):
        """Save state to Redis"""
        if self.redis_client:
            self.redis_client.set(
                self.state_key,
                json.dumps(state_data),
                ex=300  # 5 minute expiry
            )
    
    async def load_state(self) -> Optional[Dict[str, Any]]:
        """Load state from Redis"""
        if self.redis_client:
            state_json = self.redis_client.get(self.state_key)
            if state_json:
                return json.loads(state_json)
        return None
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client and hasattr(self.redis_client, 'close'):
            self.redis_client.close()

class InMemoryRedis:
    """In-memory Redis replacement for demo"""
    def __init__(self):
        self.data = {}
    
    def ping(self):
        return True
    
    def set(self, key: str, value: str, ex: int = None):
        self.data[key] = value
    
    def get(self, key: str) -> Optional[str]:
        return self.data.get(key)
    
    def delete(self, key: str):
        self.data.pop(key, None)
