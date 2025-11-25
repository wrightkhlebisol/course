"""
Application-specific metrics collector.
Tracks log processing, queue depths, and business metrics.
"""
import time
import random
from typing import Dict
import structlog

logger = structlog.get_logger()

class AppMetricsCollector:
    """Collects application-specific metrics"""
    
    def __init__(self, registry):
        self.registry = registry
        self._setup_metrics()
        self._counters = {
            'messages_processed': 0,
            'messages_failed': 0,
            'bytes_processed': 0
        }
        logger.info("app_metrics_collector_initialized")
    
    def _setup_metrics(self):
        """Setup application metrics"""
        # Processing metrics
        self.registry.register_counter(
            "messages_processed_total",
            "Total messages processed",
            labels=["status", "source"]
        )
        self.registry.register_counter(
            "messages_failed_total",
            "Total messages failed"
        )
        self.registry.register_counter(
            "bytes_processed_total",
            "Total bytes processed"
        )
        
        # Queue metrics
        self.registry.register_gauge(
            "queue_depth",
            "Current queue depth",
            labels=["queue_name"]
        )
        self.registry.register_gauge(
            "consumer_lag",
            "Consumer lag in messages",
            labels=["consumer_group"]
        )
        
        # Latency metrics
        self.registry.register_histogram(
            "message_processing_duration_seconds",
            "Message processing duration",
            labels=["operation"]
        )
        
        # Export metrics
        self.registry.register_counter(
            "metrics_exported_total",
            "Total metrics exported",
            labels=["backend"]
        )
        self.registry.register_counter(
            "metric_export_errors_total",
            "Total metric export errors",
            labels=["backend"]
        )
    
    def record_message_processed(self, status: str = "success", 
                                 source: str = "default",
                                 bytes_count: int = 100):
        """Record a processed message"""
        self.registry.inc_counter(
            "messages_processed_total",
            labels={"status": status, "source": source}
        )
        
        if status == "success":
            self._counters['messages_processed'] += 1
            self._counters['bytes_processed'] += bytes_count
            self.registry.inc_counter("bytes_processed_total", bytes_count)
        else:
            self._counters['messages_failed'] += 1
            self.registry.inc_counter("messages_failed_total")
    
    def record_processing_duration(self, operation: str, duration: float):
        """Record processing duration"""
        self.registry.observe_histogram(
            "message_processing_duration_seconds",
            duration,
            labels={"operation": operation}
        )
    
    def set_queue_depth(self, queue_name: str, depth: int):
        """Set queue depth"""
        self.registry.set_gauge(
            "queue_depth",
            depth,
            labels={"queue_name": queue_name}
        )
    
    def set_consumer_lag(self, consumer_group: str, lag: int):
        """Set consumer lag"""
        self.registry.set_gauge(
            "consumer_lag",
            lag,
            labels={"consumer_group": consumer_group}
        )
    
    def record_export(self, backend: str, success: bool):
        """Record metric export"""
        if success:
            self.registry.inc_counter(
                "metrics_exported_total",
                labels={"backend": backend}
            )
        else:
            self.registry.inc_counter(
                "metric_export_errors_total",
                labels={"backend": backend}
            )
    
    def get_counters(self) -> Dict[str, int]:
        """Get current counter values"""
        return self._counters.copy()
    
    def get_queue_depths(self) -> Dict[str, float]:
        """Get current queue depths from registry"""
        queue_depths = {}
        all_metrics = self.registry.get_all_metrics()
        metric_prefix = f"{self.registry.namespace}_queue_depth"
        
        for key, value in all_metrics.items():
            if key.startswith(metric_prefix):
                # Extract queue_name from key like "log_processor_queue_depth{queue_name=high_priority}"
                if "queue_name=" in key:
                    queue_name = key.split("queue_name=")[1].split("}")[0]
                    queue_depths[queue_name] = value
        
        return queue_depths
    
    def simulate_activity(self):
        """Simulate log processing activity"""
        # Simulate message processing
        for _ in range(random.randint(5, 15)):
            status = "success" if random.random() > 0.1 else "failed"
            source = random.choice(["web", "api", "database", "queue"])
            bytes_count = random.randint(100, 5000)
            
            self.record_message_processed(status, source, bytes_count)
            
            # Record processing duration
            duration = random.uniform(0.01, 0.5)
            self.record_processing_duration("process", duration)
        
        # Update queue depths
        for queue_name in ["high_priority", "normal", "low_priority"]:
            depth = random.randint(0, 1000)
            self.set_queue_depth(queue_name, depth)
        
        # Update consumer lag
        for group in ["consumer_group_1", "consumer_group_2"]:
            lag = random.randint(0, 500)
            self.set_consumer_lag(group, lag)
