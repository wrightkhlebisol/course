import asyncio
import aioredis
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
from src.models import MetricPoint, MetricsSnapshot, SystemMetrics, ApplicationMetrics

logger = structlog.get_logger(__name__)

class MetricsAggregator:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.metric_buffers = defaultdict(lambda: deque(maxlen=1000))
        self.running = False
        self.alert_manager = None
        
    async def start(self):
        """Start the metrics aggregator"""
        self.redis_client = await aioredis.create_redis_pool(self.redis_url)
        self.running = True
        logger.info("Started metrics aggregator")
        
        # Start background aggregation task
        asyncio.create_task(self._aggregation_loop())
    
    async def ingest_metric(self, metric: MetricPoint):
        """Ingest a single metric point"""
        key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in metric.tags.items())}"
        self.metric_buffers[key].append(metric)
        
        # Store in Redis for real-time access
        await self._store_metric_in_redis(metric)
        
        # Check for alerts if alert manager is available
        if self.alert_manager:
            await self.alert_manager.check_metric(metric)
    
    async def _store_metric_in_redis(self, metric: MetricPoint):
        """Store metric in Redis for real-time queries"""
        key = f"metric:{metric.name}"
        data = {
            "value": metric.value,
            "timestamp": metric.timestamp.isoformat(),
            "tags": str(metric.tags),
            "type": metric.metric_type.value
        }
        
        # Convert dict to key-value pairs for hmset
        hmset_args = []
        for k, v in data.items():
            hmset_args.extend([k, v])
        await self.redis_client.hmset(key, *hmset_args)
        await self.redis_client.expire(key, 3600)  # 1 hour TTL
    
    async def _aggregation_loop(self):
        """Background loop for aggregating metrics"""
        while self.running:
            try:
                await self._process_aggregations()
                await asyncio.sleep(10)  # Aggregate every 10 seconds
            except Exception as e:
                logger.error("Error in aggregation loop", error=str(e))
                await asyncio.sleep(1)
    
    async def _process_aggregations(self):
        """Process metric aggregations"""
        current_time = datetime.now()
        
        for metric_key, buffer in self.metric_buffers.items():
            if not buffer:
                continue
                
            # Calculate aggregations for different time windows
            metrics_1m = [m for m in buffer if current_time - m.timestamp <= timedelta(minutes=1)]
            metrics_5m = [m for m in buffer if current_time - m.timestamp <= timedelta(minutes=5)]
            
            if metrics_1m:
                avg_1m = sum(m.value for m in metrics_1m) / len(metrics_1m)
                await self._store_aggregation(metric_key, "1m", avg_1m, current_time)
            
            if metrics_5m:
                avg_5m = sum(m.value for m in metrics_5m) / len(metrics_5m)
                await self._store_aggregation(metric_key, "5m", avg_5m, current_time)
    
    async def _store_aggregation(self, metric_key: str, window: str, value: float, timestamp: datetime):
        """Store aggregated metric value"""
        key = f"agg:{metric_key}:{window}"
        data = {
            "value": value,
            "timestamp": timestamp.isoformat(),
            "window": window
        }
        
        # Convert dict to key-value pairs for hmset
        hmset_args = []
        for k, v in data.items():
            hmset_args.extend([k, v])
        await self.redis_client.hmset(key, *hmset_args)
        await self.redis_client.expire(key, 86400)  # 24 hour TTL
    
    async def get_recent_metrics(self, metric_name: str, minutes: int = 5) -> List[MetricPoint]:
        """Get recent metrics for a specific metric name"""
        key_pattern = f"metric:{metric_name}"
        keys = await self.redis_client.keys(f"{key_pattern}*")
        
        metrics = []
        for key in keys:
            data = await self.redis_client.hgetall(key)
            if data:
                metrics.append(MetricPoint(
                    name=metric_name,
                    value=float(data.get('value', 0)),
                    timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                    tags=eval(data.get('tags', '{}')),
                    metric_type=data.get('type', 'gauge')
                ))
        
        # Filter by time window
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in metrics if m.timestamp >= cutoff_time]
    
    async def get_current_snapshot(self) -> Dict:
        """Get current metrics snapshot"""
        # Get latest system metrics
        system_keys = await self.redis_client.keys("metric:system.*")
        system_data = {}
        
        for key in system_keys:
            data = await self.redis_client.hgetall(key)
            if data:
                metric_name = key.decode().replace("metric:", "")
                # Convert bytes to string if needed
                value = data.get(b'value', data.get('value', 0))
                if isinstance(value, bytes):
                    value = value.decode()
                system_data[metric_name] = float(value)
        
        # Get latest application metrics
        app_keys = await self.redis_client.keys("metric:application.*")
        app_data = {}
        
        for key in app_keys:
            data = await self.redis_client.hgetall(key)
            if data:
                metric_name = key.decode().replace("metric:", "")
                # Convert bytes to string if needed
                value = data.get(b'value', data.get('value', 0))
                if isinstance(value, bytes):
                    value = value.decode()
                app_data[metric_name] = float(value)
        
        return {
            "system_metrics": system_data,
            "application_metrics": app_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stop(self):
        """Stop the aggregator"""
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Stopped metrics aggregator")
