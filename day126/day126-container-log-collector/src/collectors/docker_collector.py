import docker
from docker import APIClient
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
import logging
import os

logger = logging.getLogger(__name__)

class DockerLogCollector:
    """Collects logs from Docker containers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self.active_streams = {}
        self.running = False
        
    def connect(self):
        """Connect to Docker daemon"""
        # Save and clear all Docker-related environment variables
        env_backup = {}
        docker_env_vars = ['DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_CONFIG', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH']
        for var in docker_env_vars:
            env_backup[var] = os.environ.pop(var, None)
        
        try:
            socket_path = self.config.get('socket_path', '/var/run/docker.sock')
            
            # Try using http+unix:// format directly (what docker library uses internally)
            try:
                base_url = f'http+unix://{socket_path.replace("/", "%2F")}'
                self.client = docker.DockerClient(base_url=base_url, use_ssh_client=False)
                self.client.ping()
                logger.info("✅ Connected to Docker daemon (using http+unix://)")
                return True
            except Exception as e1:
                logger.debug(f"http+unix:// attempt failed: {e1}")
            
            # Try standard unix:// format
            try:
                base_url = f'unix://{socket_path}'
                self.client = docker.DockerClient(base_url=base_url, use_ssh_client=False)
                self.client.ping()
                logger.info("✅ Connected to Docker daemon")
                return True
            except Exception as e2:
                logger.debug(f"unix:// attempt failed: {e2}")
            
            # Try using APIClient directly
            try:
                base_url = f'unix://{socket_path}'
                api_client = APIClient(base_url=base_url)
                api_client.ping()
                # Create DockerClient from working API client
                self.client = docker.DockerClient(base_url=base_url)
                logger.info("✅ Connected to Docker daemon (using APIClient)")
                return True
            except Exception as e3:
                logger.error(f"❌ All Docker connection attempts failed. Last error: {e3}")
                return False
        finally:
            # Restore environment variables
            for var, value in env_backup.items():
                if value is not None:
                    os.environ[var] = value
    
    def discover_containers(self) -> List[Dict]:
        """Discover running containers"""
        containers = []
        
        # Try using Docker client if available
        if self.client:
            try:
                for container in self.client.containers.list():
                    metadata = {
                        'container_id': container.id[:12],
                        'container_name': container.name,
                        'name': container.name,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'status': container.status,
                        'labels': container.labels,
                        'created': container.attrs['Created'],
                        'platform': 'docker'
                    }
                    containers.append(metadata)
                return containers
            except Exception as e:
                logger.debug(f"Container discovery via client failed: {e}")
        
        # Fallback: Use docker CLI if client is not available
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            metadata = {
                                'container_id': parts[0][:12],
                                'container_name': parts[1],
                                'name': parts[1],
                                'image': parts[2] if len(parts) > 2 else 'unknown',
                                'status': parts[3] if len(parts) > 3 else 'running',
                                'platform': 'docker'
                            }
                            containers.append(metadata)
                if containers:
                    logger.info(f"Discovered {len(containers)} containers via Docker CLI")
        except Exception as e:
            logger.debug(f"Container discovery via CLI failed: {e}")
            
        return containers
    
    async def stream_logs(self, container_id: str) -> AsyncGenerator[Dict, None]:
        """Stream logs from a specific container"""
        try:
            container = self.client.containers.get(container_id)
            metadata = self._extract_metadata(container)
            
            log_stream = container.logs(stream=True, follow=True, timestamps=True)
            
            for log_line in log_stream:
                if not self.running:
                    break
                    
                decoded = log_line.decode('utf-8').strip()
                if decoded:
                    # Parse timestamp if present
                    parts = decoded.split(' ', 1)
                    if len(parts) == 2:
                        timestamp_str, message = parts
                    else:
                        timestamp_str = datetime.utcnow().isoformat()
                        message = decoded
                    
                    log_entry = {
                        'timestamp': timestamp_str,
                        'message': message,
                        'source': 'docker',
                        **metadata
                    }
                    
                    yield log_entry
                    await asyncio.sleep(0)  # Allow other tasks to run
                    
        except Exception as e:
            logger.error(f"Log streaming error for {container_id}: {e}")
    
    def _extract_metadata(self, container) -> Dict:
        """Extract metadata from container"""
        return {
            'container_id': container.id[:12],
            'container_name': container.name,
            'image': container.image.tags[0] if container.image.tags else 'unknown',
            'labels': container.labels,
        }
    
    async def start_collection(self, log_queue: asyncio.Queue):
        """Start collecting logs from all containers"""
        self.running = True
        logger.info("Starting Docker log collection...")
        
        while self.running:
            containers = self.discover_containers()
            logger.info(f"Discovered {len(containers)} Docker containers")
            
            # Start streams for new containers
            for container in containers:
                container_id = container['container_id']
                if container_id not in self.active_streams:
                    task = asyncio.create_task(
                        self._collect_container_logs(container_id, log_queue)
                    )
                    self.active_streams[container_id] = task
            
            await asyncio.sleep(self.config.get('poll_interval', 5))
    
    async def _collect_container_logs(self, container_id: str, log_queue: asyncio.Queue):
        """Collect logs from single container"""
        try:
            async for log_entry in self.stream_logs(container_id):
                await log_queue.put(log_entry)
        except Exception as e:
            logger.error(f"Collection error for {container_id}: {e}")
        finally:
            if container_id in self.active_streams:
                del self.active_streams[container_id]
    
    def stop_collection(self):
        """Stop log collection"""
        self.running = False
        for task in self.active_streams.values():
            task.cancel()
        self.active_streams.clear()
        logger.info("Docker log collection stopped")
