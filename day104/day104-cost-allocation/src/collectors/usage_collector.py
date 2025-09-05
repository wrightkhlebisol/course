import asyncio
import psutil
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import json
import random

class UsageCollector:
    def __init__(self, cost_engine, config: Dict[str, Any]):
        self.cost_engine = cost_engine
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.collection_interval = 30  # seconds
        self.running = False

    async def start_collection(self):
        """Start continuous usage collection"""
        self.running = True
        self.logger.info("Starting usage collection...")
        
        # Start different collection tasks
        tasks = [
            self._collect_compute_usage(),
            self._collect_storage_usage(),
            self._collect_ingestion_usage(),
            self._collect_query_usage()
        ]
        
        await asyncio.gather(*tasks)

    async def stop_collection(self):
        """Stop usage collection"""
        self.running = False
        self.logger.info("Stopping usage collection...")

    async def _collect_compute_usage(self):
        """Collect CPU and memory usage per tenant"""
        while self.running:
            try:
                # Simulate multi-tenant compute usage
                tenants = ['engineering', 'product', 'operations']
                
                for tenant in tenants:
                    # Simulate CPU usage (in CPU-hours)
                    cpu_usage = random.uniform(0.1, 2.0) * (self.collection_interval / 3600.0)
                    
                    from cost_engine.core import ResourceUsage
                    usage = ResourceUsage(
                        tenant_id=tenant,
                        resource_type='compute',
                        amount=cpu_usage,
                        unit='cpu-hours',
                        timestamp=datetime.now(),
                        metadata={
                            'cpu_cores': random.randint(1, 4),
                            'memory_gb': random.uniform(1.0, 8.0)
                        }
                    )
                    
                    await self.cost_engine.track_usage(usage)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error collecting compute usage: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_storage_usage(self):
        """Collect storage usage per tenant"""
        storage_state = {
            'engineering': 100.0,  # Starting GB
            'product': 50.0,
            'operations': 75.0
        }
        
        while self.running:
            try:
                for tenant, current_storage in storage_state.items():
                    # Simulate storage growth
                    growth = random.uniform(-1.0, 5.0)  # GB change
                    storage_state[tenant] = max(0, current_storage + growth)
                    
                    from cost_engine.core import ResourceUsage
                    usage = ResourceUsage(
                        tenant_id=tenant,
                        resource_type='storage',
                        amount=storage_state[tenant],
                        unit='GB',
                        timestamp=datetime.now(),
                        metadata={
                            'growth': growth,
                            'retention_days': random.choice([7, 30, 90, 365])
                        }
                    )
                    
                    await self.cost_engine.track_usage(usage)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error collecting storage usage: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_ingestion_usage(self):
        """Collect log ingestion usage per tenant"""
        while self.running:
            try:
                tenants = ['engineering', 'product', 'operations']
                
                for tenant in tenants:
                    # Simulate variable ingestion rates
                    if tenant == 'engineering':
                        base_rate = random.uniform(5.0, 15.0)  # GB per collection interval
                    elif tenant == 'product':
                        base_rate = random.uniform(2.0, 8.0)
                    else:  # operations
                        base_rate = random.uniform(3.0, 10.0)
                    
                    # Add some business hours variation
                    hour = datetime.now().hour
                    if 9 <= hour <= 17:  # Business hours
                        multiplier = random.uniform(1.2, 2.0)
                    else:
                        multiplier = random.uniform(0.3, 0.8)
                    
                    ingestion_amount = base_rate * multiplier * (self.collection_interval / 3600.0)
                    
                    from cost_engine.core import ResourceUsage
                    usage = ResourceUsage(
                        tenant_id=tenant,
                        resource_type='ingestion',
                        amount=ingestion_amount,
                        unit='GB',
                        timestamp=datetime.now(),
                        metadata={
                            'source_services': random.randint(3, 12),
                            'peak_rate': base_rate * multiplier,
                            'business_hours': 9 <= hour <= 17
                        }
                    )
                    
                    await self.cost_engine.track_usage(usage)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error collecting ingestion usage: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_query_usage(self):
        """Collect query execution usage per tenant"""
        while self.running:
            try:
                tenants = ['engineering', 'product', 'operations']
                
                for tenant in tenants:
                    # Simulate query patterns
                    if tenant == 'engineering':
                        query_count = random.randint(50, 200)  # More debugging queries
                    elif tenant == 'product':
                        query_count = random.randint(20, 100)  # Analytics queries
                    else:  # operations
                        query_count = random.randint(100, 300)  # Monitoring queries
                    
                    from cost_engine.core import ResourceUsage
                    usage = ResourceUsage(
                        tenant_id=tenant,
                        resource_type='queries',
                        amount=query_count,
                        unit='queries',
                        timestamp=datetime.now(),
                        metadata={
                            'avg_duration_ms': random.uniform(100, 5000),
                            'complex_queries': random.randint(0, query_count // 10),
                            'cached_hits': random.randint(0, query_count // 3)
                        }
                    )
                    
                    await self.cost_engine.track_usage(usage)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error collecting query usage: {e}")
                await asyncio.sleep(self.collection_interval)
