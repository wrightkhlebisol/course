"""
Main application orchestrator
"""

import asyncio
import threading
import yaml
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from flink.stream_processor import FlinkStreamProcessor
from sources.rabbitmq_source import RabbitMQSource
from sinks.dashboard_sink import DashboardSink
from api.web_server import app, update_stats, add_alert, broadcast_update
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamProcessingApp:
    """Main application orchestrator"""
    
    def __init__(self, config_path: str = "config/flink_config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Override sensitive values with environment variables if set
        if 'sources' in self.config and 'rabbitmq' in self.config['sources']:
            if os.getenv('RABBITMQ_USERNAME'):
                self.config['sources']['rabbitmq']['username'] = os.getenv('RABBITMQ_USERNAME')
            if os.getenv('RABBITMQ_PASSWORD'):
                self.config['sources']['rabbitmq']['password'] = os.getenv('RABBITMQ_PASSWORD')
            
        self.processor = FlinkStreamProcessor(self.config)
        self.source = RabbitMQSource(self.config['sources']['rabbitmq'])
        self.dashboard_sink = DashboardSink(
            port=self.config['outputs']['dashboard']['websocket_port']
        )
        
        self.running = False
        self.event_loop = None
        
    def process_event(self, log_entry: dict):
        """Process incoming log event"""
        alerts = self.processor.process_event(log_entry)
        
        # Send alerts to dashboard
        for alert in alerts:
            add_alert(alert)
            
            # Broadcast via WebSocket (schedule from thread)
            if self.event_loop and self.event_loop.is_running():
                def schedule_alert():
                    asyncio.create_task(self.dashboard_sink.send_alert(alert))
                self.event_loop.call_soon_threadsafe(schedule_alert)
            
    async def statistics_updater(self):
        """Periodically update statistics"""
        while self.running:
            stats = self.processor.get_statistics()
            update_stats(stats)
            
            # Broadcast to WebSocket clients
            await self.dashboard_sink.send_statistics(stats)
            
            await asyncio.sleep(2)
            
    def run_source(self):
        """Run message source in separate thread"""
        try:
            self.source.connect()
            self.source.consume(self.process_event)
        except Exception as e:
            logger.error(f"Source error: {e}")
            
    async def run_async_components(self):
        """Run async components"""
        await self.dashboard_sink.start()
        await self.statistics_updater()
        
    def start(self):
        """Start all components"""
        logger.info("🚀 Starting Flink Stream Processing Application")
        
        self.running = True
        
        # Start source in separate thread
        source_thread = threading.Thread(target=self.run_source, daemon=True)
        source_thread.start()
        
        # Start web server in separate thread
        web_thread = threading.Thread(
            target=lambda: uvicorn.run(
                app, 
                host=self.config['web']['host'],
                port=self.config['web']['port'],
                log_level="info"
            ),
            daemon=True
        )
        web_thread.start()
        
        # Run async components
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.event_loop = loop
        
        try:
            loop.run_until_complete(self.run_async_components())
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
            self.running = False
        finally:
            loop.close()
            self.event_loop = None


if __name__ == "__main__":
    stream_app = StreamProcessingApp()
    stream_app.start()
