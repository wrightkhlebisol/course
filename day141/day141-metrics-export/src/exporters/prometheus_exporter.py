"""
Prometheus metrics exporter.
Exposes /metrics endpoint in OpenMetrics format.
"""
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import structlog

logger = structlog.get_logger()

class PrometheusExporter:
    """Exports metrics in Prometheus format"""
    
    def __init__(self, registry):
        self.registry = registry
        self.prom_registry = registry.get_prometheus_registry()
        logger.info("prometheus_exporter_initialized")
    
    def get_metrics(self) -> Response:
        """Generate Prometheus metrics response"""
        try:
            metrics_output = generate_latest(self.prom_registry)
            return Response(
                content=metrics_output,
                media_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error("metrics_generation_failed", error=str(e))
            return Response(content=b"", status_code=500)
    
    def get_metrics_text(self) -> str:
        """Get metrics as text for display"""
        return generate_latest(self.prom_registry).decode('utf-8')
