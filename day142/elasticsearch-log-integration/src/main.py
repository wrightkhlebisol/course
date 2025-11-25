import asyncio
import json
import yaml
import sys
import threading
from pathlib import Path
from elasticsearch import AsyncElasticsearch
import structlog

# Import components
sys.path.append(str(Path(__file__).parent))
from indexer.log_indexer import LogIndexer
from indexer.index_manager import IndexManager
from indexer.consumer import IndexingConsumer
from search.search_engine import SearchEngine
import api.app as api_app

# Setup logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

class ElasticsearchIntegration:
    """Main application coordinator"""
    
    def __init__(self, config_path: str = 'config/elasticsearch_config.yaml'):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.es = None
        self.indexer = None
        self.index_manager = None
        self.search_engine = None
        self.consumer = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("initializing_elasticsearch_integration")
        
        # Connect to Elasticsearch
        self.es = AsyncElasticsearch(
            hosts=self.config['elasticsearch']['hosts']
        )
        
        # Test connection
        if not await self.es.ping():
            raise ConnectionError("Cannot connect to Elasticsearch")
        
        logger.info("elasticsearch_connected")
        
        # Initialize managers
        self.index_manager = IndexManager(self.es, self.config['elasticsearch'])
        await self.index_manager.create_index_template()
        await self.index_manager.ensure_today_index()
        
        # Initialize indexer
        self.indexer = LogIndexer(self.es, self.config['elasticsearch'])
        
        # Initialize search engine
        self.search_engine = SearchEngine(self.es, self.config['elasticsearch'])
        
        # Set API references
        api_app.search_engine = self.search_engine
        api_app.index_manager = self.index_manager
        api_app.log_indexer = self.indexer
        
        logger.info("all_components_initialized")
        
    async def start_indexing(self):
        """Start background indexing"""
        # Start periodic flush
        asyncio.create_task(self.indexer.periodic_flush())
        logger.info("indexing_started")
        
    def start_consumer(self, loop):
        """Start RabbitMQ consumer in background thread"""
        self.consumer = IndexingConsumer(
            self.config['rabbitmq'],
            self.indexer
        )
        
        def consumer_thread():
            """Run consumer in separate thread"""
            if self.consumer.connect():
                def on_message(ch, method, properties, body):
                    try:
                        log_entry = json.loads(body)
                        # Schedule coroutine in main event loop
                        future = asyncio.run_coroutine_threadsafe(
                            self.indexer.add_log(log_entry),
                            loop
                        )
                        # Wait for completion (with timeout)
                        future.result(timeout=5)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error("message_processing_failed", error=str(e))
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
                self.consumer.start_consuming(on_message)
            else:
                logger.error("failed_to_start_consumer")
        
        thread = threading.Thread(target=consumer_thread, daemon=True)
        thread.start()
        logger.info("consumer_thread_started")
    
    async def close(self):
        """Cleanup resources"""
        if self.indexer:
            await self.indexer.flush_batch()
        if self.consumer:
            self.consumer.close()
        if self.es:
            await self.es.close()
        logger.info("cleanup_complete")

async def main():
    integration = ElasticsearchIntegration()
    
    try:
        await integration.initialize()
        await integration.start_indexing()
        
        # Get the current event loop for consumer thread
        loop = asyncio.get_event_loop()
        
        # Start RabbitMQ consumer in background thread
        integration.start_consumer(loop)
        
        logger.info("elasticsearch_integration_ready")
        
        # Start API server
        import uvicorn
        config = uvicorn.Config(
            api_app.app,
            host=integration.config['api']['host'],
            port=integration.config['api']['port'],
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("shutting_down")
    finally:
        await integration.close()

if __name__ == "__main__":
    asyncio.run(main())
