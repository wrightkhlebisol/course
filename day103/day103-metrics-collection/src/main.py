import asyncio
import structlog
import signal
import sys
from typing import Optional
from config.metrics_config import MetricsConfig
from src.collectors.system_collector import SystemMetricsCollector
from src.collectors.application_collector import ApplicationMetricsCollector
from src.aggregators.metrics_aggregator import MetricsAggregator
from src.alerts.alert_manager import AlertManager
from src.api.metrics_api import MetricsAPI
import uvicorn

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

class MetricsCollectionSystem:
    def __init__(self):
        self.config = MetricsConfig.from_env()
        self.aggregator = None
        self.alert_manager = None
        self.system_collector = None
        self.app_collector = None
        self.api = None
        self.running = False
        
    async def start(self):
        """Start the metrics collection system"""
        logger.info("Starting Metrics Collection System")
        
        # Initialize components
        self.aggregator = MetricsAggregator(self.config.redis_url)
        await self.aggregator.start()
        
        self.alert_manager = AlertManager(self.config)
        await self.alert_manager.start()
        
        # Setup API
        self.api = MetricsAPI(self.aggregator, self.alert_manager, self.config)
        
        # Add alert handler for WebSocket broadcasting
        self.alert_manager.add_alert_handler(self.api.broadcast_alert)
        
        # Connect alert manager to aggregator for metric checking
        self.aggregator.alert_manager = self.alert_manager
        
        # Start collectors
        self.system_collector = SystemMetricsCollector(self.config.collection_interval)
        self.app_collector = ApplicationMetricsCollector()
        
        # Connect collectors to aggregator
        self.system_collector.aggregator = self.aggregator
        self.app_collector.aggregator = self.aggregator
        
        # Start collection tasks
        self.running = True
        asyncio.create_task(self.system_collector.start_collection())
        asyncio.create_task(self.app_collector.start_collection())
        
        logger.info("Metrics Collection System started successfully")
        
        # Start API server
        config = uvicorn.Config(
            self.api.app,
            host=self.config.api_host,
            port=self.config.api_port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    async def stop(self):
        """Stop the metrics collection system"""
        logger.info("Stopping Metrics Collection System")
        
        self.running = False
        
        if self.system_collector:
            self.system_collector.stop_collection()
        
        if self.app_collector:
            self.app_collector.stop_collection()
        
        if self.alert_manager:
            await self.alert_manager.stop()
        
        if self.aggregator:
            await self.aggregator.stop()
        
        logger.info("Metrics Collection System stopped")

async def main():
    system = MetricsCollectionSystem()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(system.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        await system.stop()
    except Exception as e:
        logger.error("Fatal error in metrics system", error=str(e))
        await system.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
