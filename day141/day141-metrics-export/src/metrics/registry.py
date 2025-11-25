"""
Unified metrics registry for all monitoring backends.
Manages counters, gauges, histograms, and summaries.
"""
from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time
import threading
import structlog

logger = structlog.get_logger()

@dataclass
class MetricDefinition:
    """Definition of a metric with metadata"""
    name: str
    metric_type: str  # counter, gauge, histogram, summary
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # for histograms

class UnifiedMetricsRegistry:
    """
    Central registry managing metrics for multiple backends.
    Provides high-level API for instrumenting application code.
    """
    
    def __init__(self, namespace: str = "log_processor"):
        self.namespace = namespace
        self.prom_registry = CollectorRegistry()
        self._metrics = {}
        self._metric_values = defaultdict(float)
        self._labels_cache = {}
        self._cardinality_limit = 10000
        self._lock = threading.RLock()
        
        logger.info("metrics_registry_initialized", namespace=namespace)
        
    def register_counter(self, name: str, description: str, 
                        labels: List[str] = None) -> None:
        """Register a counter metric"""
        labels = labels or []
        full_name = f"{self.namespace}_{name}"
        
        if full_name not in self._metrics:
            self._metrics[full_name] = {
                'type': 'counter',
                'description': description,
                'labels': labels,
                'prometheus': Counter(
                    full_name, description, labels, registry=self.prom_registry
                )
            }
            logger.info("counter_registered", name=full_name, labels=labels)
    
    def register_gauge(self, name: str, description: str,
                      labels: List[str] = None) -> None:
        """Register a gauge metric"""
        labels = labels or []
        full_name = f"{self.namespace}_{name}"
        
        if full_name not in self._metrics:
            self._metrics[full_name] = {
                'type': 'gauge',
                'description': description,
                'labels': labels,
                'prometheus': Gauge(
                    full_name, description, labels, registry=self.prom_registry
                )
            }
            logger.info("gauge_registered", name=full_name, labels=labels)
    
    def register_histogram(self, name: str, description: str,
                          labels: List[str] = None,
                          buckets: tuple = None) -> None:
        """Register a histogram metric"""
        labels = labels or []
        buckets = buckets or (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
        full_name = f"{self.namespace}_{name}"
        
        if full_name not in self._metrics:
            self._metrics[full_name] = {
                'type': 'histogram',
                'description': description,
                'labels': labels,
                'buckets': buckets,
                'prometheus': Histogram(
                    full_name, description, labels, buckets=buckets,
                    registry=self.prom_registry
                )
            }
            logger.info("histogram_registered", name=full_name, labels=labels)
    
    def inc_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None) -> None:
        """Increment a counter"""
        full_name = f"{self.namespace}_{name}"
        labels = labels or {}
        
        if full_name in self._metrics:
            metric = self._metrics[full_name]
            if metric['type'] == 'counter':
                if labels:
                    metric['prometheus'].labels(**labels).inc(value)
                else:
                    metric['prometheus'].inc(value)
                    
                # Store for Datadog export
                label_key = self._make_label_key(full_name, labels)
                with self._lock:
                    self._metric_values[label_key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge value"""
        full_name = f"{self.namespace}_{name}"
        labels = labels or {}
        
        if full_name in self._metrics:
            metric = self._metrics[full_name]
            if metric['type'] == 'gauge':
                if labels:
                    metric['prometheus'].labels(**labels).set(value)
                else:
                    metric['prometheus'].set(value)
                    
                # Store for Datadog export
                label_key = self._make_label_key(full_name, labels)
                with self._lock:
                    self._metric_values[label_key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a value in histogram"""
        full_name = f"{self.namespace}_{name}"
        labels = labels or {}
        
        if full_name in self._metrics:
            metric = self._metrics[full_name]
            if metric['type'] == 'histogram':
                if labels:
                    metric['prometheus'].labels(**labels).observe(value)
                else:
                    metric['prometheus'].observe(value)
    
    def get_prometheus_registry(self) -> CollectorRegistry:
        """Get Prometheus collector registry"""
        return self.prom_registry
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics for export"""
        with self._lock:
            return dict(self._metric_values)
    
    def _make_label_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create unique key from metric name and labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def check_cardinality(self) -> Dict[str, int]:
        """Check metric cardinality"""
        cardinality = defaultdict(int)
        for key in self._metric_values.keys():
            metric_name = key.split('{')[0]
            cardinality[metric_name] += 1
        return dict(cardinality)

# Global registry instance
global_registry = UnifiedMetricsRegistry()
