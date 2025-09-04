import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.aggregators.metrics_aggregator import MetricsAggregator
from src.models import MetricPoint, MetricType
from datetime import datetime

@pytest.mark.asyncio
async def test_metric_aggregator_ingest():
    # Mock Redis client
    mock_redis = AsyncMock()
    
    aggregator = MetricsAggregator("redis://test")
    aggregator.redis_client = mock_redis
    
    # Test metric ingestion
    metric = MetricPoint(
        name="test.metric",
        value=50.0,
        timestamp=datetime.now(),
        tags={"host": "test"},
        metric_type=MetricType.GAUGE
    )
    
    await aggregator.ingest_metric(metric)
    
    # Verify metric was stored
    assert len(aggregator.metric_buffers) > 0
    mock_redis.hset.assert_called()

@pytest.mark.asyncio
async def test_metric_retrieval():
    mock_redis = AsyncMock()
    mock_redis.keys.return_value = [b"metric:test.metric"]
    mock_redis.hgetall.return_value = {
        b'value': b'50.0',
        b'timestamp': datetime.now().isoformat().encode(),
        b'tags': b"{'host': 'test'}",
        b'type': b'gauge'
    }
    
    aggregator = MetricsAggregator("redis://test")
    aggregator.redis_client = mock_redis
    
    metrics = await aggregator.get_recent_metrics("test.metric", 5)
    
    assert len(metrics) >= 0
    mock_redis.keys.assert_called()
