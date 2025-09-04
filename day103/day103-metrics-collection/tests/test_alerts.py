import pytest
import asyncio
from src.alerts.alert_manager import AlertManager
from src.models import MetricPoint, MetricType, AlertLevel
from config.metrics_config import MetricsConfig
from datetime import datetime

@pytest.mark.asyncio
async def test_alert_generation():
    config = MetricsConfig()
    alert_manager = AlertManager(config)
    
    # Create high CPU metric
    high_cpu_metric = MetricPoint(
        name="system.cpu.usage_percent",
        value=95.0,  # Above critical threshold
        timestamp=datetime.now(),
        tags={"host": "test"},
        metric_type=MetricType.GAUGE
    )
    
    await alert_manager.check_metric(high_cpu_metric)
    
    # Check that alert was generated
    active_alerts = await alert_manager.get_active_alerts()
    assert len(active_alerts) > 0
    
    alert = active_alerts[0]
    assert alert.level == AlertLevel.CRITICAL
    assert "CPU" in alert.message

@pytest.mark.asyncio
async def test_alert_resolution():
    config = MetricsConfig()
    alert_manager = AlertManager(config)
    
    # Generate an alert
    metric = MetricPoint(
        name="system.memory.usage_percent",
        value=98.0,
        timestamp=datetime.now(),
        tags={"host": "test"},
        metric_type=MetricType.GAUGE
    )
    
    await alert_manager.check_metric(metric)
    active_alerts = await alert_manager.get_active_alerts()
    
    if active_alerts:
        alert_id = active_alerts[0].id
        
        # Resolve the alert
        await alert_manager.resolve_alert(alert_id)
        
        # Check it's no longer active
        remaining_alerts = await alert_manager.get_active_alerts()
        alert_ids = [a.id for a in remaining_alerts]
        assert alert_id not in alert_ids
