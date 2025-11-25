"""Integration tests for metrics export"""
import pytest
from src.metrics.registry import UnifiedMetricsRegistry
from src.exporters.prometheus_exporter import PrometheusExporter
from src.collectors.system_metrics import SystemMetricsCollector

@pytest.mark.asyncio
async def test_system_metrics_collection():
    registry = UnifiedMetricsRegistry("test")
    collector = SystemMetricsCollector(registry)
    metrics = collector.collect()
    
    assert 'cpu_percent' in metrics
    assert 'memory_percent' in metrics
    assert metrics['cpu_percent'] >= 0

def test_prometheus_export():
    registry = UnifiedMetricsRegistry("test")
    registry.register_counter("test_metric", "Test")
    registry.inc_counter("test_metric", 42)
    
    exporter = PrometheusExporter(registry)
    response = exporter.get_metrics()
    
    assert response.status_code == 200
    assert b"test_test_metric" in response.body
