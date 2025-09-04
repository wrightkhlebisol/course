import pytest
import asyncio
from src.collectors.system_collector import SystemMetricsCollector

@pytest.mark.asyncio
async def test_system_metrics_collection():
    collector = SystemMetricsCollector(collection_interval=1)
    
    # Test metric collection
    metrics = await collector.collect_metrics()
    
    assert metrics.cpu_usage >= 0
    assert metrics.memory_usage >= 0
    assert metrics.disk_usage >= 0
    assert len(metrics.load_average) == 3
    assert metrics.uptime > 0

@pytest.mark.asyncio  
async def test_collector_start_stop():
    collector = SystemMetricsCollector(collection_interval=1)
    
    # Start collection in background
    task = asyncio.create_task(collector.start_collection())
    
    # Let it run briefly
    await asyncio.sleep(2)
    
    # Stop collection
    collector.stop_collection()
    
    # Wait for task to complete
    await asyncio.sleep(1)
    task.cancel()
    
    assert not collector.running
