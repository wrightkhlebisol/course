import redis
import json
import os
from typing import Optional, Any

class RedisClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = redis.from_url(self.redis_url, decode_responses=True)
    
    async def get_flag(self, flag_name: str) -> Optional[dict]:
        """Get feature flag from cache"""
        try:
            data = self.client.get(f"flag:{flag_name}")
            return json.loads(data) if data else None
        except Exception:
            return None
    
    async def set_flag(self, flag_name: str, flag_data: dict, ttl: int = 300):
        """Cache feature flag data"""
        try:
            self.client.setex(f"flag:{flag_name}", ttl, json.dumps(flag_data))
        except Exception:
            pass
    
    async def invalidate_flag(self, flag_name: str):
        """Remove flag from cache"""
        try:
            self.client.delete(f"flag:{flag_name}")
        except Exception:
            pass
    
    async def increment_evaluation_count(self, flag_name: str, user_context: str = "anonymous"):
        """Track flag evaluation metrics"""
        try:
            key = f"flag_eval:{flag_name}:{user_context}"
            self.client.incr(key)
            self.client.expire(key, 86400)  # 24 hours
        except Exception:
            pass

redis_client = RedisClient()
