"""
Main Application - Coordinates metric extraction, writing, and API
"""
import asyncio
import logging
import signal
import sys
import os
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extractors.metrics_extractor import MetricsExtractor
from writers.timescale_writer import TimescaleWriter
from generators.log_generator import LogGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricsPipeline:
    """Coordinates the metrics extraction and storage pipeline"""
    
    def __init__(self):
        self.extractor = MetricsExtractor()
        self.writer = TimescaleWriter({
            'host': 'localhost',
            'port': 5432,
            'database': 'metrics',
            'user': 'postgres',
            'password': 'password'
        })
        self.generator = LogGenerator()
        self.running = False
    
    def setup(self):
        """Initialize database schema"""
        logger.info("🔧 Setting up database schema...")
        self.writer.setup_schema()
        logger.info("✅ Schema setup complete")
    
    async def process_logs(self, duration: int = 60):
        """Process logs and extract metrics"""
        logger.info(f"🔄 Starting log processing for {duration} seconds...")
        self.running = True
        
        start_time = datetime.now()
        total_logs = 0
        total_metrics = 0
        
        try:
            while self.running:
                # Generate test logs
                logs = self.generator.generate_batch(count=10)
                
                for log in logs:
                    # Extract metrics
                    metrics = self.extractor.extract_from_log(log)
                    
                    # Write to database
                    for metric in metrics:
                        self.writer.add_metric({
                            'measurement': metric.measurement,
                            'tags': metric.tags,
                            'fields': metric.fields,
                            'timestamp': metric.timestamp
                        })
                    
                    total_logs += 1
                    total_metrics += len(metrics)
                
                # Periodic status
                if total_logs % 100 == 0:
                    logger.info(f"📊 Processed {total_logs} logs, extracted {total_metrics} metrics")
                
                await asyncio.sleep(0.1)  # 100ms between batches
                
                # Check duration
                if (datetime.now() - start_time).total_seconds() >= duration:
                    break
        
        except KeyboardInterrupt:
            logger.info("⚠️  Interrupted by user")
        finally:
            self.writer.flush()
            logger.info(f"✅ Processing complete: {total_logs} logs → {total_metrics} metrics")
    
    def stop(self):
        """Stop the pipeline"""
        logger.info("🛑 Stopping pipeline...")
        self.running = False
        self.writer.close()

async def main():
    """Main entry point"""
    pipeline = MetricsPipeline()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        pipeline.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize
    pipeline.setup()
    
    # Process logs
    await pipeline.process_logs(duration=60)
    
    # Cleanup
    pipeline.stop()

if __name__ == '__main__':
    asyncio.run(main())
