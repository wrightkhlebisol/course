import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from cache.manager import SmartCache

@pytest.fixture
def cache():
    temp_dir = Path(tempfile.mkdtemp())
    cache_instance = SmartCache(str(temp_dir), max_size_mb=10)
    
    yield cache_instance
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_cache_set_get(cache):
    test_data = {"test": "data", "numbers": [1, 2, 3]}
    
    await cache.set("test_key", test_data)
    result = await cache.get("test_key")
    
    assert result == test_data

@pytest.mark.asyncio
async def test_cache_miss(cache):
    result = await cache.get("nonexistent_key")
    assert result is None

@pytest.mark.asyncio
async def test_cache_stats(cache):
    # Generate some cache activity
    await cache.set("key1", "data1")
    await cache.get("key1")  # Hit
    await cache.get("key2")  # Miss
    
    stats = await cache.get_stats()
    
    assert stats['hits'] >= 1
    assert stats['misses'] >= 1
    assert stats['hit_rate'] >= 0

@pytest.mark.asyncio
async def test_cache_eviction(cache):
    # Fill cache beyond memory limit
    for i in range(1500):  # More than the 1000 entry limit
        await cache.set(f"key_{i}", f"data_{i}")
    
    # Check that eviction occurred
    assert len(cache.memory_cache) <= 1000
    assert cache.cache_stats['evictions'] > 0
