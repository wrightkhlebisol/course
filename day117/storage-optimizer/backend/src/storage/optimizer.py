import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import random

class StorageTier(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"

@dataclass
class LogEntry:
    id: str
    content: str
    timestamp: datetime
    size_bytes: int
    access_count: int
    last_accessed: datetime
    tier: StorageTier
    compression_ratio: float = 1.0
    cost_per_gb_month: float = 0.0

@dataclass
class StorageMetrics:
    total_size_gb: float
    hot_size_gb: float
    warm_size_gb: float
    cold_size_gb: float
    monthly_cost: float
    compression_savings: float
    tier_distribution: Dict[str, int]

class StorageOptimizer:
    def __init__(self):
        self.log_entries: Dict[str, LogEntry] = {}
        self.optimization_running = False
        self.metrics = StorageMetrics(0, 0, 0, 0, 0, 0, {})
        
        # Cost per GB per month for different tiers
        self.tier_costs = {
            StorageTier.HOT: 0.23,    # SSD storage
            StorageTier.WARM: 0.05,   # HDD storage  
            StorageTier.COLD: 0.01    # Archive storage
        }
        
    async def initialize(self):
        """Initialize with sample log data"""
        await self._generate_sample_data()
        asyncio.create_task(self._optimization_loop())
        
    async def _generate_sample_data(self):
        """Generate realistic log data for demonstration"""
        log_types = ['error', 'info', 'debug', 'warning']
        services = ['api-gateway', 'user-service', 'payment', 'analytics']
        
        for i in range(1000):
            created_time = datetime.now() - timedelta(days=random.randint(0, 90))
            access_frequency = random.randint(0, 50) if created_time > datetime.now() - timedelta(days=7) else random.randint(0, 5)
            
            entry = LogEntry(
                id=f"log_{i:04d}",
                content=f"{random.choice(log_types)} from {random.choice(services)}: sample log message {i}",
                timestamp=created_time,
                size_bytes=random.randint(100, 2000),
                access_count=access_frequency,
                last_accessed=created_time + timedelta(hours=random.randint(1, 168)),
                tier=StorageTier.HOT,  # All start in hot storage
                cost_per_gb_month=self.tier_costs[StorageTier.HOT]
            )
            
            self.log_entries[entry.id] = entry
            
    async def optimize_storage(self) -> Dict:
        """Run storage optimization across all entries"""
        optimized_count = 0
        cost_savings = 0
        
        for log_id, entry in self.log_entries.items():
            old_cost = self._calculate_entry_cost(entry)
            
            # Optimization logic
            optimized = await self._optimize_entry(entry)
            if optimized:
                new_cost = self._calculate_entry_cost(entry)
                cost_savings += (old_cost - new_cost)
                optimized_count += 1
                
        await self._update_metrics()
        
        return {
            "optimized_entries": optimized_count,
            "cost_savings": cost_savings,
            "total_entries": len(self.log_entries)
        }
        
    async def _optimize_entry(self, entry: LogEntry) -> bool:
        """Optimize a single log entry"""
        days_old = (datetime.now() - entry.timestamp).days
        access_frequency = entry.access_count / max(days_old, 1)
        
        current_tier = entry.tier
        new_tier = current_tier
        
        # Tier optimization rules
        if days_old > 60 and access_frequency < 0.1:
            new_tier = StorageTier.COLD
        elif days_old > 7 and access_frequency < 1.0:
            new_tier = StorageTier.WARM
        elif access_frequency > 5.0:
            new_tier = StorageTier.HOT
            
        # Apply compression based on content type
        if 'debug' in entry.content and entry.compression_ratio == 1.0:
            entry.compression_ratio = 0.3  # 70% compression
        elif 'info' in entry.content and entry.compression_ratio == 1.0:
            entry.compression_ratio = 0.5  # 50% compression
            
        if new_tier != current_tier:
            entry.tier = new_tier
            entry.cost_per_gb_month = self.tier_costs[new_tier]
            return True
            
        return False
        
    def _calculate_entry_cost(self, entry: LogEntry) -> float:
        """Calculate monthly cost for a log entry"""
        size_gb = (entry.size_bytes * entry.compression_ratio) / (1024**3)
        return size_gb * entry.cost_per_gb_month
        
    async def _update_metrics(self):
        """Update storage metrics"""
        total_size = 0
        hot_size = warm_size = cold_size = 0
        total_cost = 0
        compression_savings = 0
        tier_count = {tier.value: 0 for tier in StorageTier}
        
        for entry in self.log_entries.values():
            original_size = entry.size_bytes / (1024**3)
            compressed_size = original_size * entry.compression_ratio
            
            total_size += compressed_size
            total_cost += self._calculate_entry_cost(entry)
            compression_savings += (original_size - compressed_size)
            
            tier_count[entry.tier.value] += 1
            
            if entry.tier == StorageTier.HOT:
                hot_size += compressed_size
            elif entry.tier == StorageTier.WARM:
                warm_size += compressed_size
            else:
                cold_size += compressed_size
                
        self.metrics = StorageMetrics(
            total_size_gb=total_size,
            hot_size_gb=hot_size,
            warm_size_gb=warm_size,
            cold_size_gb=cold_size,
            monthly_cost=total_cost,
            compression_savings=compression_savings,
            tier_distribution=tier_count
        )
        
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            await asyncio.sleep(30)  # Run every 30 seconds for demo
            if not self.optimization_running:
                self.optimization_running = True
                try:
                    await self.optimize_storage()
                finally:
                    self.optimization_running = False
                    
    async def get_metrics(self) -> Dict:
        """Get current storage metrics"""
        await self._update_metrics()
        return asdict(self.metrics)
        
    async def get_log_entries(self, limit: int = 100) -> List[Dict]:
        """Get sample log entries with their optimization status"""
        entries = list(self.log_entries.values())[:limit]
        return [asdict(entry) for entry in entries]
