import asyncio
import yaml
import logging
import sys
from pathlib import Path
from typing import Dict

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from collectors.docker_collector import DockerLogCollector
from collectors.kubernetes_collector import KubernetesLogCollector
from enrichment.metadata_enricher import MetadataEnricher
from stream.multiplexer import LogStreamMultiplexer
from api.server import LogAPIServer

import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContainerLogCollectionSystem:
    """Main container log collection system"""
    
    def __init__(self, config_path: str = None):
        # Get the base directory (parent of src)
        base_dir = Path(__file__).parent.parent
        if config_path is None:
            config_path = base_dir / 'config' / 'collector_config.yaml'
        else:
            config_path = Path(config_path)
        
        # Load configuration
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.enricher = MetadataEnricher()
        self.multiplexer = LogStreamMultiplexer(self.config['collection'])
        
        # Initialize collectors
        self.docker_collector = None
        self.k8s_collector = None
        
        if self.config['docker']['enabled']:
            self.docker_collector = DockerLogCollector(self.config['docker'])
            if self.docker_collector.connect():
                logger.info("Docker collector initialized")
        
        if self.config['kubernetes']['enabled']:
            self.k8s_collector = KubernetesLogCollector(self.config['kubernetes'])
            if self.k8s_collector.connect():
                logger.info("Kubernetes collector initialized")
        
        # Initialize API server
        self.api_server = LogAPIServer(
            self.multiplexer,
            self.docker_collector,
            self.k8s_collector,
            self.enricher
        )
        
        self.tasks = []
    
    async def process_and_enrich(self, log_entry: Dict):
        """Process and enrich log entries before multiplexing"""
        enriched = self.enricher.enrich(log_entry)
        await self.multiplexer.add_log(enriched)
    
    async def run(self):
        """Run the collection system"""
        logger.info("🚀 Starting Container Log Collection System")
        
        # Start multiplexer
        self.tasks.append(asyncio.create_task(self.multiplexer.start()))
        
        # Start collectors
        if self.docker_collector:
            self.tasks.append(
                asyncio.create_task(
                    self.docker_collector.start_collection(self.multiplexer.log_queue)
                )
            )
        
        if self.k8s_collector:
            self.tasks.append(
                asyncio.create_task(
                    self.k8s_collector.start_collection(self.multiplexer.log_queue)
                )
            )
        
        # Start API server in background
        config = uvicorn.Config(
            self.api_server.app,
            host=self.config['dashboard']['host'],
            port=self.config['dashboard']['port'],
            log_level="info"
        )
        server = uvicorn.Server(config)
        self.tasks.append(asyncio.create_task(server.serve()))
        
        logger.info(f"📊 Dashboard: http://localhost:{self.config['dashboard']['port']}")
        logger.info("✨ System is running. Press Ctrl+C to stop.")
        
        try:
            await asyncio.gather(*self.tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()
    
    def stop(self):
        """Stop all components"""
        if self.docker_collector:
            self.docker_collector.stop_collection()
        if self.k8s_collector:
            self.k8s_collector.stop_collection()
        self.multiplexer.stop()
        
        for task in self.tasks:
            task.cancel()

def main():
    system = ContainerLogCollectionSystem()
    try:
        asyncio.run(system.run())
    except KeyboardInterrupt:
        logger.info("System stopped")

if __name__ == "__main__":
    main()
