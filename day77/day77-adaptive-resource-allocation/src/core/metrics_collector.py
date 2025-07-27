import psutil
import time
import json
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: float
    queue_depth: int = 0
    processing_latency_ms: float = 0.0

class MetricsCollector:
    def __init__(self, config: Dict):
        self.config = config
        self.metrics_history = deque(maxlen=1000)
        self.running = False
        self.collection_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
    def start_collection(self):
        """Start continuous metrics collection"""
        self.running = True
        self.collection_thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.collection_thread.start()
        print("✅ Metrics collection started")
        
    def stop_collection(self):
        """Stop metrics collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join()
        print("⏹️ Metrics collection stopped")
        
    def _collect_loop(self):
        """Main collection loop"""
        interval = self.config.get('interval_seconds', 5)
        
        while self.running:
            try:
                metrics = self._collect_system_metrics()
                with self.lock:
                    self.metrics_history.append(metrics)
                time.sleep(interval)
            except Exception as e:
                print(f"❌ Error collecting metrics: {e}")
                time.sleep(interval)
                
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Load average
        load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        
        # Connection count
        try:
            connections = len(psutil.net_connections())
        except:
            connections = 0
            
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage_percent=disk_usage_percent,
            network_bytes_sent=net_io.bytes_sent,
            network_bytes_recv=net_io.bytes_recv,
            active_connections=connections,
            load_average=load_avg
        )
        
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get most recent metrics"""
        with self.lock:
            return self.metrics_history[-1] if self.metrics_history else None
            
    def get_metrics_history(self, minutes: int = 15) -> List[SystemMetrics]:
        """Get metrics history for specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                metrics for metrics in self.metrics_history 
                if metrics.timestamp >= cutoff_time
            ]
            
    def get_metrics_summary(self) -> Dict:
        """Get summary statistics of recent metrics"""
        recent_metrics = self.get_metrics_history(15)
        
        if not recent_metrics:
            return {}
            
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        return {
            'avg_cpu': sum(cpu_values) / len(cpu_values),
            'max_cpu': max(cpu_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'max_memory': max(memory_values),
            'sample_count': len(recent_metrics),
            'collection_period_minutes': 15
        }
