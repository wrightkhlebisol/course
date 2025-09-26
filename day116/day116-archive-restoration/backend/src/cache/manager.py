import asyncio
import json
import time
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CacheEntry:
    def __init__(self, key: str, data: Any, ttl: int = 3600):
        self.key = key
        self.data = data
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 1
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        return time.time() > (self.created_at + self.ttl)
    
    def access(self):
        self.access_count += 1
        self.last_accessed = time.time()

class SmartCache:
    def __init__(self, cache_dir: str, max_size_mb: int = 1024):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
    async def get(self, key: str) -> Optional[Any]:
        """Get cached data with LRU and disk fallback"""
        
        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            
            if not entry.is_expired():
                entry.access()
                self.cache_stats['hits'] += 1
                return entry.data
            else:
                # Remove expired entry
                del self.memory_cache[key]
        
        # Check disk cache
        disk_data = await self._get_from_disk(key)
        if disk_data:
            # Load back into memory cache
            await self.set(key, disk_data, ttl=3600)
            self.cache_stats['hits'] += 1
            return disk_data
        
        self.cache_stats['misses'] += 1
        return None
    
    async def set(self, key: str, data: Any, ttl: int = 3600):
        """Set cached data with intelligent eviction"""
        
        # Store in memory
        entry = CacheEntry(key, data, ttl)
        self.memory_cache[key] = entry
        
        # Store on disk for persistence
        await self._store_to_disk(key, data)
        
        # Check if eviction needed
        await self._maybe_evict()
    
    async def _get_from_disk(self, key: str) -> Optional[Any]:
        """Retrieve data from disk cache"""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                # Check if expired
                if time.time() <= cache_data.get('expires_at', 0):
                    return cache_data.get('data')
                else:
                    # Remove expired file
                    cache_file.unlink()
                    
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
                
        return None
    
    async def _store_to_disk(self, key: str, data: Any):
        """Store data to disk cache"""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
        
        try:
            cache_data = {
                'key': key,
                'data': data,
                'created_at': time.time(),
                'expires_at': time.time() + 3600  # 1 hour disk TTL
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, default=str)
                
        except Exception as e:
            logger.warning(f"Failed to store cache file {cache_file}: {e}")
    
    async def _maybe_evict(self):
        """Evict least recently used entries if cache is full"""
        
        # Simple memory-based eviction
        if len(self.memory_cache) > 1000:  # Max 1000 entries in memory
            # Sort by last accessed time
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove oldest 20%
            to_remove = len(sorted_entries) // 5
            for i in range(to_remove):
                key = sorted_entries[i][0]
                del self.memory_cache[key]
                self.cache_stats['evictions'] += 1
    
    def _hash_key(self, key: str) -> str:
        """Create hash of cache key for filename"""
        return hashlib.md5(key.encode()).hexdigest()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'total_entries': len(self.memory_cache),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions']
        }
    
    async def clear(self):
        """Clear all cached data"""
        self.memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
