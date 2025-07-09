import asyncio
import logging
import os
import sys
from src.backend.nodes.log_processor import LogProcessorNode
from src.backend.web_service import FailoverWebService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main application entry point"""
    # Get configuration from environment
    node_id = os.getenv('NODE_ID', 'primary')
    node_port = int(os.getenv('NODE_PORT', '8001'))
    is_primary = os.getenv('IS_PRIMARY', 'true').lower() == 'true'
    
    logger.info(f"Starting node: {node_id}, port: {node_port}, primary: {is_primary}")
    
    # Create log processor node
    node = LogProcessorNode(node_id, node_port, is_primary)
    
    # Start node
    await node.start()
    
    # Create web service
    web_service = FailoverWebService(node)
    
    try:
        # Start web server
        await web_service.start_server()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Cleanup
        await node.stop()

if __name__ == "__main__":
    asyncio.run(main())
