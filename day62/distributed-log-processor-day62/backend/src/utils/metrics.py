"""
Metrics Collection and Monitoring
"""
import time
import psutil
import asyncio
from typing import Dict, Any
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()

class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(lambda: deque(maxlen=1000))
        self.start_time = time.time()
    
    async def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric"""
        self.counters[name] += value
    
    async def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        self.gauges[name] = value
    
    async def record_histogram(self, name: str, value: float):
        """Record a histogram value"""
        self.histograms[name].append(value)
    
    async def get_resource_utilization(self) -> float:
        """Get combined resource utilization (CPU + Memory)"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Weighted combination (CPU weighted more heavily)
            combined = (cpu_percent * 0.7 + memory_percent * 0.3) / 100.0
            
            await self.set_gauge("cpu_percent", cpu_percent)
            await self.set_gauge("memory_percent", memory_percent)
            await self.set_gauge("resource_utilization", combined)
            
            return combined
            
        except Exception as e:
            logger.error("Failed to get resource utilization", error=str(e))
            return 0.5  # Default moderate utilization
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        # Update resource metrics
        await self.get_resource_utilization()
        
        # Calculate histogram statistics
        histogram_stats = {}
        for name, values in self.histograms.items():
            if values:
                histogram_stats[name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": histogram_stats,
            "uptime_seconds": time.time() - self.start_time,
            "timestamp": time.time()
        }
