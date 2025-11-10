from kubernetes import client, config
from kubernetes.client.rest import ApiException
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class KubernetesLogCollector:
    """Collects logs from Kubernetes pods"""
    
    def __init__(self, collector_config: Dict):
        self.config = collector_config
        self.core_v1 = None
        self.active_streams = {}
        self.running = False
    
    def connect(self):
        """Connect to Kubernetes API"""
        try:
            config_file = self.config.get('config_file')
            if config_file:
                config.load_kube_config(config_file=config_file)
            else:
                config.load_incluster_config()
            
            self.core_v1 = client.CoreV1Api()
            # Test connection
            self.core_v1.list_namespace()
            logger.info("✅ Connected to Kubernetes API")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Kubernetes not available: {e}")
            return False
    
    def discover_pods(self) -> List[Dict]:
        """Discover running pods"""
        if not self.core_v1:
            return []
        
        pods = []
        namespaces = self.config.get('namespaces', ['default'])
        label_selector = self.config.get('label_selector')
        
        try:
            for namespace in namespaces:
                pod_list = self.core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector
                )
                
                for pod in pod_list.items:
                    if pod.status.phase == 'Running':
                        metadata = {
                            'pod_name': pod.metadata.name,
                            'namespace': pod.metadata.namespace,
                            'labels': pod.metadata.labels or {},
                            'node': pod.spec.node_name,
                            'containers': [c.name for c in pod.spec.containers],
                            'platform': 'kubernetes'
                        }
                        pods.append(metadata)
        except ApiException as e:
            logger.error(f"Pod discovery error: {e}")
        
        return pods
    
    async def stream_pod_logs(self, pod_name: str, namespace: str, 
                             container: str) -> AsyncGenerator[Dict, None]:
        """Stream logs from a specific pod container"""
        try:
            # Get pod metadata
            pod = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            metadata = {
                'pod_name': pod_name,
                'namespace': namespace,
                'container': container,
                'labels': pod.metadata.labels or {},
                'node': pod.spec.node_name,
                'source': 'kubernetes'
            }
            
            # Stream logs
            log_stream = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                follow=True,
                timestamps=True,
                _preload_content=False
            )
            
            for line in log_stream.stream():
                if not self.running:
                    break
                
                decoded = line.decode('utf-8').strip()
                if decoded:
                    # Parse K8s log format: timestamp message
                    parts = decoded.split(' ', 1)
                    if len(parts) == 2:
                        timestamp_str, message = parts
                    else:
                        timestamp_str = datetime.utcnow().isoformat()
                        message = decoded
                    
                    log_entry = {
                        'timestamp': timestamp_str,
                        'message': message,
                        **metadata
                    }
                    
                    yield log_entry
                    await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"Pod log streaming error: {e}")
    
    async def start_collection(self, log_queue: asyncio.Queue):
        """Start collecting logs from all pods"""
        self.running = True
        logger.info("Starting Kubernetes log collection...")
        
        while self.running:
            pods = self.discover_pods()
            logger.info(f"Discovered {len(pods)} Kubernetes pods")
            
            # Start streams for new pods
            for pod_info in pods:
                for container in pod_info['containers']:
                    stream_id = f"{pod_info['namespace']}/{pod_info['pod_name']}/{container}"
                    if stream_id not in self.active_streams:
                        task = asyncio.create_task(
                            self._collect_pod_logs(
                                pod_info['pod_name'],
                                pod_info['namespace'],
                                container,
                                log_queue
                            )
                        )
                        self.active_streams[stream_id] = task
            
            await asyncio.sleep(self.config.get('poll_interval', 5))
    
    async def _collect_pod_logs(self, pod_name: str, namespace: str, 
                                container: str, log_queue: asyncio.Queue):
        """Collect logs from single pod container"""
        try:
            async for log_entry in self.stream_pod_logs(pod_name, namespace, container):
                await log_queue.put(log_entry)
        except Exception as e:
            logger.error(f"Collection error for {namespace}/{pod_name}/{container}: {e}")
        finally:
            stream_id = f"{namespace}/{pod_name}/{container}"
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
    
    def stop_collection(self):
        """Stop log collection"""
        self.running = False
        for task in self.active_streams.values():
            task.cancel()
        self.active_streams.clear()
        logger.info("Kubernetes log collection stopped")
