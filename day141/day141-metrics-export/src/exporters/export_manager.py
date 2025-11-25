"""
Manages metrics export to multiple backends.
Orchestrates Prometheus and Datadog exporters.
"""
import asyncio
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()

class MetricsExportManager:
    """Manages export to multiple monitoring backends"""
    
    def __init__(self, registry, prometheus_exporter=None, datadog_exporter=None):
        self.registry = registry
        self.prometheus_exporter = prometheus_exporter
        self.datadog_exporter = datadog_exporter
        self.export_interval = 30  # seconds
        self._running = False
        self._export_task = None
        
        logger.info("export_manager_initialized")
    
    async def start_export_loop(self):
        """Start continuous export loop"""
        self._running = True
        self._export_task = asyncio.create_task(self._export_loop())
        logger.info("export_loop_started", interval=self.export_interval)
    
    async def stop_export_loop(self):
        """Stop export loop"""
        self._running = False
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
        logger.info("export_loop_stopped")
    
    async def _export_loop(self):
        """Main export loop"""
        while self._running:
            try:
                await self.export_metrics()
                await asyncio.sleep(self.export_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("export_loop_error", error=str(e))
                await asyncio.sleep(5)
    
    async def export_metrics(self) -> Dict[str, bool]:
        """Export metrics to all configured backends"""
        results = {}
        
        # Export to Datadog if configured
        if self.datadog_exporter:
            try:
                metrics = self.registry.get_all_metrics()
                metrics_list = [
                    {
                        'name': name,
                        'value': value,
                        'type': 'gauge',
                        'tags': ['env:production']
                    }
                    for name, value in metrics.items()
                ]
                
                success = self.datadog_exporter.send_metrics_batch(metrics_list)
                results['datadog'] = success
                
                if success:
                    logger.info("metrics_exported_to_datadog", count=len(metrics_list))
                    
            except Exception as e:
                logger.error("datadog_export_failed", error=str(e))
                results['datadog'] = False
        
        # Prometheus exports via /metrics endpoint (pull model)
        results['prometheus'] = self.prometheus_exporter is not None
        
        return results
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics"""
        return {
            'backends_configured': {
                'prometheus': self.prometheus_exporter is not None,
                'datadog': self.datadog_exporter is not None
            },
            'export_interval': self.export_interval,
            'running': self._running
        }
