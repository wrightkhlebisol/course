"""
Datadog metrics exporter.
Pushes metrics via DogStatsD and HTTP API.
"""
from datadog import initialize, api
from datadog import statsd
import time
from typing import Dict, Any, List
import structlog
import asyncio

logger = structlog.get_logger()

class DatadogExporter:
    """Exports metrics to Datadog"""
    
    def __init__(self, api_key: str, app_key: str, 
                 statsd_host: str = "localhost", statsd_port: int = 8125):
        self.api_key = api_key
        self.app_key = app_key
        
        # Initialize Datadog
        options = {
            'api_key': api_key,
            'app_key': app_key
        }
        initialize(**options)
        
        # Configure StatsD
        statsd.host = statsd_host
        statsd.port = statsd_port
        
        self.metrics_buffer = []
        self.last_flush = time.time()
        self.flush_interval = 10  # seconds
        
        logger.info("datadog_exporter_initialized",
                   statsd_host=statsd_host, statsd_port=statsd_port)
    
    def gauge(self, metric: str, value: float, tags: List[str] = None) -> None:
        """Send gauge metric"""
        try:
            statsd.gauge(metric, value, tags=tags or [])
        except Exception as e:
            logger.error("gauge_send_failed", metric=metric, error=str(e))
    
    def increment(self, metric: str, value: float = 1, tags: List[str] = None) -> None:
        """Send counter increment"""
        try:
            statsd.increment(metric, value, tags=tags or [])
        except Exception as e:
            logger.error("increment_send_failed", metric=metric, error=str(e))
    
    def histogram(self, metric: str, value: float, tags: List[str] = None) -> None:
        """Send histogram value"""
        try:
            statsd.histogram(metric, value, tags=tags or [])
        except Exception as e:
            logger.error("histogram_send_failed", metric=metric, error=str(e))
    
    def timing(self, metric: str, value: float, tags: List[str] = None) -> None:
        """Send timing metric"""
        try:
            statsd.timing(metric, value, tags=tags or [])
        except Exception as e:
            logger.error("timing_send_failed", metric=metric, error=str(e))
    
    def send_metrics_batch(self, metrics: List[Dict[str, Any]]) -> bool:
        """Send batch of metrics via HTTP API"""
        try:
            current_time = int(time.time())
            series = []
            
            for metric in metrics:
                series.append({
                    'metric': metric['name'],
                    'points': [[current_time, metric['value']]],
                    'type': metric.get('type', 'gauge'),
                    'tags': metric.get('tags', [])
                })
            
            if series:
                api.Metric.send(series)
                logger.info("metrics_batch_sent", count=len(series))
                return True
                
        except Exception as e:
            logger.error("batch_send_failed", error=str(e))
            return False
    
    def should_flush(self) -> bool:
        """Check if buffer should be flushed"""
        return (time.time() - self.last_flush) >= self.flush_interval
