import asyncio
import structlog
from datetime import datetime
from typing import List, Dict, Callable
from src.models import Alert, AlertLevel, MetricPoint
from config.metrics_config import MetricsConfig

logger = structlog.get_logger(__name__)

class AlertManager:
    def __init__(self, config: MetricsConfig):
        self.config = config
        self.active_alerts = {}
        self.alert_handlers = []
        self.running = False
        
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add a handler for alert notifications"""
        self.alert_handlers.append(handler)
    
    async def start(self):
        """Start the alert manager"""
        self.running = True
        logger.info("Started alert manager")
    
    async def check_metric(self, metric: MetricPoint):
        """Check if a metric violates any thresholds"""
        alerts = []
        
        # Check system metrics
        if metric.name == "system.cpu.usage_percent":
            alerts.extend(self._check_cpu_alerts(metric))
        elif metric.name == "system.memory.usage_percent":
            alerts.extend(self._check_memory_alerts(metric))
        elif metric.name == "system.disk.usage_percent":
            alerts.extend(self._check_disk_alerts(metric))
        
        # Process any new alerts
        for alert in alerts:
            await self._handle_alert(alert)
    
    def _check_cpu_alerts(self, metric: MetricPoint) -> List[Alert]:
        """Check CPU usage alerts"""
        alerts = []
        
        if metric.value >= self.config.cpu_critical_threshold:
            alert = Alert(
                id=f"cpu_critical_{int(metric.timestamp.timestamp())}",
                metric_name=metric.name,
                level=AlertLevel.CRITICAL,
                threshold=self.config.cpu_critical_threshold,
                current_value=metric.value,
                message=f"Critical CPU usage: {metric.value:.1f}%",
                timestamp=metric.timestamp
            )
            alerts.append(alert)
        elif metric.value >= self.config.cpu_warning_threshold:
            alert = Alert(
                id=f"cpu_warning_{int(metric.timestamp.timestamp())}",
                metric_name=metric.name,
                level=AlertLevel.WARNING,
                threshold=self.config.cpu_warning_threshold,
                current_value=metric.value,
                message=f"High CPU usage: {metric.value:.1f}%",
                timestamp=metric.timestamp
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_memory_alerts(self, metric: MetricPoint) -> List[Alert]:
        """Check memory usage alerts"""
        alerts = []
        
        if metric.value >= self.config.memory_critical_threshold:
            alert = Alert(
                id=f"memory_critical_{int(metric.timestamp.timestamp())}",
                metric_name=metric.name,
                level=AlertLevel.CRITICAL,
                threshold=self.config.memory_critical_threshold,
                current_value=metric.value,
                message=f"Critical memory usage: {metric.value:.1f}%",
                timestamp=metric.timestamp
            )
            alerts.append(alert)
        elif metric.value >= self.config.memory_warning_threshold:
            alert = Alert(
                id=f"memory_warning_{int(metric.timestamp.timestamp())}",
                metric_name=metric.name,
                level=AlertLevel.WARNING,
                threshold=self.config.memory_warning_threshold,
                current_value=metric.value,
                message=f"High memory usage: {metric.value:.1f}%",
                timestamp=metric.timestamp
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_disk_alerts(self, metric: MetricPoint) -> List[Alert]:
        """Check disk usage alerts"""
        alerts = []
        
        if metric.value >= self.config.disk_critical_threshold:
            alert = Alert(
                id=f"disk_critical_{int(metric.timestamp.timestamp())}",
                metric_name=metric.name,
                level=AlertLevel.CRITICAL,
                threshold=self.config.disk_critical_threshold,
                current_value=metric.value,
                message=f"Critical disk usage: {metric.value:.1f}%",
                timestamp=metric.timestamp
            )
            alerts.append(alert)
        elif metric.value >= self.config.disk_warning_threshold:
            alert = Alert(
                id=f"disk_warning_{int(metric.timestamp.timestamp())}",
                metric_name=metric.name,
                level=AlertLevel.WARNING,
                threshold=self.config.disk_warning_threshold,
                current_value=metric.value,
                message=f"High disk usage: {metric.value:.1f}%",
                timestamp=metric.timestamp
            )
            alerts.append(alert)
        
        return alerts
    
    async def _handle_alert(self, alert: Alert):
        """Handle a new alert"""
        # Avoid duplicate alerts
        if alert.id in self.active_alerts:
            return
        
        self.active_alerts[alert.id] = alert
        logger.warn("Alert triggered", 
                   alert_id=alert.id,
                   level=alert.level.value,
                   message=alert.message,
                   value=alert.current_value)
        
        # Notify all handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error("Error in alert handler", error=str(e))
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            del self.active_alerts[alert_id]
            logger.info("Alert resolved", alert_id=alert_id)
    
    async def stop(self):
        """Stop the alert manager"""
        self.running = False
        logger.info("Stopped alert manager")
