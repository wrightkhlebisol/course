import asyncio
import random
import structlog
from datetime import datetime
from typing import Dict, List
from src.models import ApplicationMetrics, MetricPoint, MetricType

logger = structlog.get_logger(__name__)

class ApplicationMetricsCollector:
    def __init__(self):
        self.logs_processed_total = 0
        self.active_connections = 0
        self.queue_depth = 0
        self.error_count = 0
        self.response_times = []
        self.running = False
        self.aggregator = None
        
    async def start_collection(self):
        """Start application metrics collection"""
        self.running = True
        logger.info("Starting application metrics collection")
        
        # Simulate some baseline activity
        asyncio.create_task(self._simulate_activity())
        
        while self.running:
            try:
                metrics = await self.collect_metrics()
                await self.emit_metrics(metrics)
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("Error collecting application metrics", error=str(e))
                await asyncio.sleep(1)
    
    async def _simulate_activity(self):
        """Simulate realistic application activity"""
        while self.running:
            # Simulate log processing
            logs_batch = random.randint(50, 200)
            self.logs_processed_total += logs_batch
            
            # Simulate connection changes
            connection_change = random.randint(-5, 10)
            self.active_connections = max(0, self.active_connections + connection_change)
            
            # Simulate queue changes
            queue_change = random.randint(-20, 30)
            self.queue_depth = max(0, self.queue_depth + queue_change)
            
            # Simulate some errors
            if random.random() < 0.1:  # 10% chance of errors
                self.error_count += random.randint(1, 5)
            
            # Simulate response times
            response_time = random.uniform(10, 500)  # 10-500ms
            self.response_times.append(response_time)
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]  # Keep last 100
            
            await asyncio.sleep(1)
    
    async def collect_metrics(self) -> ApplicationMetrics:
        """Collect current application metrics"""
        # Calculate rates and percentiles
        logs_rate = len([t for t in self.response_times if t]) if self.response_times else 0
        error_rate = (self.error_count / max(1, self.logs_processed_total)) * 100
        p95_response_time = sorted(self.response_times)[int(0.95 * len(self.response_times))] if self.response_times else 0
        
        return ApplicationMetrics(
            logs_processed_total=self.logs_processed_total,
            logs_processed_rate=logs_rate,
            active_connections=self.active_connections,
            queue_depth=self.queue_depth,
            error_rate=error_rate,
            response_time_p95=p95_response_time,
            timestamp=datetime.now()
        )
    
    async def emit_metrics(self, metrics: ApplicationMetrics):
        """Emit metrics to aggregation layer"""
        # Convert to MetricPoint objects
        metric_points = [
            MetricPoint(
                name="application.logs.processed_total",
                value=float(metrics.logs_processed_total),
                timestamp=metrics.timestamp,
                tags={"host": "localhost"},
                metric_type=MetricType.COUNTER
            ),
            MetricPoint(
                name="application.logs.processed_rate",
                value=metrics.logs_processed_rate,
                timestamp=metrics.timestamp,
                tags={"host": "localhost"},
                metric_type=MetricType.GAUGE
            ),
            MetricPoint(
                name="application.connections.active",
                value=float(metrics.active_connections),
                timestamp=metrics.timestamp,
                tags={"host": "localhost"},
                metric_type=MetricType.GAUGE
            ),
            MetricPoint(
                name="application.queue.depth",
                value=float(metrics.queue_depth),
                timestamp=metrics.timestamp,
                tags={"host": "localhost"},
                metric_type=MetricType.GAUGE
            ),
            MetricPoint(
                name="application.error.rate",
                value=metrics.error_rate,
                timestamp=metrics.timestamp,
                tags={"host": "localhost"},
                metric_type=MetricType.GAUGE
            ),
            MetricPoint(
                name="application.response_time.p95",
                value=metrics.response_time_p95,
                timestamp=metrics.timestamp,
                tags={"host": "localhost"},
                metric_type=MetricType.GAUGE
            )
        ]
        
        # Send metrics to aggregator if available
        if self.aggregator:
            for metric_point in metric_points:
                await self.aggregator.ingest_metric(metric_point)
        
        logger.info("Collected application metrics",
                   logs_total=metrics.logs_processed_total,
                   logs_rate=metrics.logs_processed_rate,
                   connections=metrics.active_connections,
                   queue_depth=metrics.queue_depth,
                   error_rate=metrics.error_rate,
                   p95_response_time=metrics.response_time_p95)
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        logger.info("Stopped application metrics collection")
