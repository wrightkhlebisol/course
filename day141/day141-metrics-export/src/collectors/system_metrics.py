"""
System metrics collector.
Collects CPU, memory, disk, and network metrics.
"""
import psutil
import time
from typing import Dict
import structlog

logger = structlog.get_logger()

class SystemMetricsCollector:
    """Collects system-level metrics"""
    
    def __init__(self, registry):
        self.registry = registry
        self._setup_metrics()
        logger.info("system_metrics_collector_initialized")
    
    def _setup_metrics(self):
        """Setup system metrics"""
        # CPU metrics
        self.registry.register_gauge(
            "system_cpu_percent",
            "CPU usage percentage"
        )
        self.registry.register_gauge(
            "system_cpu_count",
            "Number of CPU cores"
        )
        
        # Memory metrics
        self.registry.register_gauge(
            "system_memory_used_bytes",
            "Used memory in bytes"
        )
        self.registry.register_gauge(
            "system_memory_total_bytes",
            "Total memory in bytes"
        )
        self.registry.register_gauge(
            "system_memory_percent",
            "Memory usage percentage"
        )
        
        # Disk metrics
        self.registry.register_gauge(
            "system_disk_used_bytes",
            "Disk space used in bytes"
        )
        self.registry.register_gauge(
            "system_disk_total_bytes",
            "Total disk space in bytes"
        )
    
    def collect(self) -> Dict[str, float]:
        """Collect all system metrics"""
        metrics = {}
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            self.registry.set_gauge("system_cpu_percent", cpu_percent)
            self.registry.set_gauge("system_cpu_count", cpu_count)
            
            metrics['cpu_percent'] = cpu_percent
            metrics['cpu_count'] = cpu_count
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.registry.set_gauge("system_memory_used_bytes", memory.used)
            self.registry.set_gauge("system_memory_total_bytes", memory.total)
            self.registry.set_gauge("system_memory_percent", memory.percent)
            
            metrics['memory_used_bytes'] = memory.used
            metrics['memory_total_bytes'] = memory.total
            metrics['memory_percent'] = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.registry.set_gauge("system_disk_used_bytes", disk.used)
            self.registry.set_gauge("system_disk_total_bytes", disk.total)
            
            metrics['disk_used_bytes'] = disk.used
            metrics['disk_total_bytes'] = disk.total
            
            logger.debug("system_metrics_collected", metrics=metrics)
            
        except Exception as e:
            logger.error("system_metrics_collection_failed", error=str(e))
        
        return metrics
