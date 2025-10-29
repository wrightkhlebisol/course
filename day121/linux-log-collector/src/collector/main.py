"""Main Linux Log Collector Application"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any

import yaml
import structlog
from collector.discovery.log_discovery import LogDiscoveryEngine
from collector.file_monitor.file_monitor import LogFileMonitor
from collector.batch_processor.batch_processor import BatchProcessor
from web.dashboard import start_dashboard, update_collector_stats


class LinuxLogCollector:
    def __init__(self, config_path: str = "config/collector_config.yaml"):
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        self.discovery_engine = LogDiscoveryEngine(self.config)
        self.file_monitor = LogFileMonitor(self.config)
        self.batch_processor = BatchProcessor(self.config)
        self.running = False
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load collector configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_logging(self):
        """Setup structured logging"""
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        self.logger = structlog.get_logger("collector")
    
    async def start(self):
        """Start the log collector"""
        self.logger.info("Starting Linux Log Collector", version="1.0.0")
        self.running = True
        
        # Start web dashboard immediately - don't block on discovery
        dashboard_task = asyncio.create_task(
            start_dashboard(self.config.get('monitoring', {}))
        )
        
        # Start discovery and monitoring as background tasks
        async def discovery_and_monitoring():
            # Discover log sources
            await self.discovery_engine.discover_sources()
            discovered_sources = self.discovery_engine.get_discovered_sources()
            self.logger.info("Log sources discovered", count=len(discovered_sources))
            
            # Start file monitoring after discovery
            await self.file_monitor.start_monitoring(discovered_sources)
        
        discovery_task = asyncio.create_task(discovery_and_monitoring())
        
        # Start batch processing
        batch_task = asyncio.create_task(
            self.batch_processor.start_processing(self.file_monitor.log_queue)
        )
        
        # Start stats aggregation task
        stats_task = asyncio.create_task(self._aggregate_stats())
        
        try:
            await asyncio.gather(dashboard_task, discovery_task, batch_task, stats_task)
        except KeyboardInterrupt:
            self.logger.info("Shutting down collector...")
            self.running = False
    
    async def _aggregate_stats(self):
        """Aggregate stats from all components and update dashboard"""
        while self.running:
            try:
                # Collect stats from all components
                processor_stats = self.batch_processor.get_stats() if hasattr(self.batch_processor, 'get_stats') else {}
                
                # Map processor stats to dashboard expected format
                if processor_stats:
                    processor_stats['batches_received'] = processor_stats.get('batches_sent', 0)
                
                stats = {
                    'discovery': self.discovery_engine.get_stats(),
                    'monitor': self.file_monitor.get_stats(),
                    'processor': processor_stats
                }
                
                # Update dashboard stats
                update_collector_stats(stats)
                
                await asyncio.sleep(2)  # Update every 2 seconds
            except Exception as e:
                self.logger.error("Stats aggregation error", error=str(e))
                await asyncio.sleep(5)
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal", signal=signum)
            self.running = False
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)


async def main():
    collector = LinuxLogCollector()
    collector.setup_signal_handlers()
    await collector.start()


if __name__ == "__main__":
    asyncio.run(main())
