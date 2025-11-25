"""Unit tests for metrics registry"""
import pytest
from src.metrics.registry import UnifiedMetricsRegistry

def test_register_counter():
    registry = UnifiedMetricsRegistry("test")
    registry.register_counter("test_counter", "Test counter")
    assert "test_test_counter" in registry._metrics

def test_increment_counter():
    registry = UnifiedMetricsRegistry("test")
    registry.register_counter("requests", "Request count")
    registry.inc_counter("requests", 5)
    assert registry.get_all_metrics()["test_requests"] == 5

def test_set_gauge():
    registry = UnifiedMetricsRegistry("test")
    registry.register_gauge("temperature", "Temperature")
    registry.set_gauge("temperature", 25.5)
    assert registry.get_all_metrics()["test_temperature"] == 25.5

def test_metrics_with_labels():
    registry = UnifiedMetricsRegistry("test")
    registry.register_counter("http_requests", "HTTP requests", labels=["method", "status"])
    registry.inc_counter("http_requests", labels={"method": "GET", "status": "200"})
    metrics = registry.get_all_metrics()
    assert any("http_requests" in key for key in metrics.keys())
