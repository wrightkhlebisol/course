"""Mock Log Receiver Server"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
from aiohttp import web
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for received logs
received_logs = []
stats = {
    'total_received': 0,
    'total_batches': 0,
    'start_time': datetime.now().isoformat()
}


async def receive_logs(request):
    """Receive log batches"""
    try:
        data = await request.json()
        logs = data.get('logs', [])
        
        received_logs.extend(logs)
        stats['total_received'] += len(logs)
        stats['total_batches'] += 1
        
        logger.info(
            f"Received batch with {len(logs)} logs (total: {stats['total_received']})"
        )
        
        return web.json_response({
            'status': 'ok',
            'received': len(logs),
            'total': stats['total_received']
        })
    except Exception as e:
        logger.error(f"Error receiving logs: {e}")
        return web.json_response(
            {'error': str(e)}, 
            status=500
        )


async def get_stats(request):
    """Get statistics"""
    return web.json_response({
        **stats,
        'recent_logs_count': len(received_logs),
        'uptime_seconds': (
            datetime.now() - datetime.fromisoformat(stats['start_time'])
        ).total_seconds()
    })


async def get_recent_logs(request):
    """Get recent logs"""
    limit = int(request.query.get('limit', 100))
    logs = received_logs[-limit:]
    
    return web.json_response({
        'count': len(logs),
        'logs': logs
    })


async def health_check(request):
    """Health check endpoint"""
    return web.json_response({'status': 'healthy'})


def create_app():
    """Create the web application"""
    app = web.Application()
    
    app.router.add_post('/api/logs', receive_logs)
    app.router.add_get('/api/stats', get_stats)
    app.router.add_get('/api/logs', get_recent_logs)
    app.router.add_get('/health', health_check)
    
    return app


def run_server():
    """Run the server"""
    # Get port from environment variable (for Docker) or use 8080 for standalone
    port = int(os.getenv('SERVER_PORT', '8080'))
    
    logger.info(f"Starting Mock Log Receiver on http://0.0.0.0:{port}")
    
    app = create_app()
    
    # Use web.run_app for standalone execution  
    # In Docker: port will be 8000 (mapped to 8080 on host)
    # Standalone: port will be 8080
    try:
        web.run_app(app, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        sys.exit(0)


if __name__ == '__main__':
    run_server()

