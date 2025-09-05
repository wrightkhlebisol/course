import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import logging
import redis

@dataclass
class ResourceUsage:
    tenant_id: str
    resource_type: str  # ingestion, storage, queries, compute
    amount: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

@dataclass
class CostRecord:
    tenant_id: str
    resource_type: str
    usage_amount: float
    cost_amount: float
    currency: str
    period_start: datetime
    period_end: datetime
    pricing_model: str

class AllocationMethod(Enum):
    DIRECT = "direct"
    PROPORTIONAL = "proportional"
    ACTIVITY_BASED = "activity_based"

class CostEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config['database']['path']
        self.redis_client = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            db=config['redis']['db']
        )
        self.pricing_models = config['cost_allocation']['pricing_models']
        self.shared_allocation = config['cost_allocation']['shared_allocation']
        self.tenants = config['cost_allocation']['tenants']
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for cost records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                amount REAL NOT NULL,
                unit TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                usage_amount REAL NOT NULL,
                cost_amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                pricing_model TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usage_tenant_time 
            ON usage_records(tenant_id, timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_cost_tenant_period 
            ON cost_records(tenant_id, period_start, period_end)
        ''')
        
        conn.commit()
        conn.close()

    async def track_usage(self, usage: ResourceUsage) -> bool:
        """Track resource usage for cost allocation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO usage_records 
                (tenant_id, resource_type, amount, unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                usage.tenant_id,
                usage.resource_type,
                usage.amount,
                usage.unit,
                usage.timestamp.isoformat(),
                json.dumps(usage.metadata or {})
            ))
            
            conn.commit()
            conn.close()
            
            # Update real-time metrics in Redis
            await self._update_realtime_metrics(usage)
            
            self.logger.info(f"Tracked usage: {usage.tenant_id} - {usage.resource_type}: {usage.amount} {usage.unit}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error tracking usage: {e}")
            return False

    async def _update_realtime_metrics(self, usage: ResourceUsage):
        """Update real-time metrics in Redis"""
        key_prefix = f"usage:{usage.tenant_id}:{usage.resource_type}"
        
        # Update hourly metrics
        hour_key = f"{key_prefix}:hour:{datetime.now().strftime('%Y%m%d%H')}"
        self.redis_client.incrbyfloat(hour_key, usage.amount)
        self.redis_client.expire(hour_key, 86400)  # 24 hours
        
        # Update daily metrics
        day_key = f"{key_prefix}:day:{datetime.now().strftime('%Y%m%d')}"
        self.redis_client.incrbyfloat(day_key, usage.amount)
        self.redis_client.expire(day_key, 86400 * 31)  # 31 days

    async def calculate_costs(self, start_time: datetime, end_time: datetime) -> Dict[str, Dict[str, float]]:
        """Calculate costs for all tenants in the given time period"""
        costs = {}
        
        # Get usage data for the period
        usage_data = await self._get_usage_data(start_time, end_time)
        
        # Calculate direct costs
        for tenant_id in self.tenants.keys():
            costs[tenant_id] = {}
            tenant_usage = [u for u in usage_data if u['tenant_id'] == tenant_id]
            
            # Calculate direct resource costs
            for resource_type, pricing in self.pricing_models.items():
                resource_usage = [u for u in tenant_usage if u['resource_type'] == resource_type]
                total_usage = sum(u['amount'] for u in resource_usage)
                
                if 'price_per_gb' in pricing:
                    cost = total_usage * pricing['price_per_gb']
                elif 'price_per_gb_month' in pricing:
                    # Calculate monthly cost based on storage duration
                    days = (end_time - start_time).days
                    cost = total_usage * pricing['price_per_gb_month'] * (days / 30.0)
                elif 'price_per_query' in pricing:
                    cost = total_usage * pricing['price_per_query']
                elif 'price_per_cpu_hour' in pricing:
                    cost = total_usage * pricing['price_per_cpu_hour']
                else:
                    cost = 0.0
                
                costs[tenant_id][resource_type] = cost

        # Apply shared cost allocation
        shared_costs = await self._calculate_shared_costs(usage_data, start_time, end_time)
        
        for tenant_id in costs.keys():
            if 'shared' not in costs[tenant_id]:
                costs[tenant_id]['shared'] = 0.0
            costs[tenant_id]['shared'] += shared_costs.get(tenant_id, 0.0)
            
            # Calculate total cost
            costs[tenant_id]['total'] = sum(costs[tenant_id].values())

        # Store cost records
        await self._store_cost_records(costs, start_time, end_time)
        
        return costs

    async def _get_usage_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Retrieve usage data from database for the specified period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tenant_id, resource_type, amount, unit, timestamp, metadata
            FROM usage_records
            WHERE timestamp >= ? AND timestamp <= ?
        ''', (start_time.isoformat(), end_time.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        usage_data = []
        for row in rows:
            usage_data.append({
                'tenant_id': row[0],
                'resource_type': row[1],
                'amount': row[2],
                'unit': row[3],
                'timestamp': datetime.fromisoformat(row[4]),
                'metadata': json.loads(row[5]) if row[5] else {}
            })
        
        return usage_data

    async def _calculate_shared_costs(self, usage_data: List[Dict[str, Any]], 
                                    start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Calculate shared infrastructure costs allocation"""
        shared_costs = {}
        total_shared_cost = 100.0  # Simulated shared infrastructure cost
        
        if self.shared_allocation['method'] == 'proportional':
            # Calculate total usage by resource type
            total_usage = {}
            tenant_usage = {}
            
            for usage in usage_data:
                resource_type = usage['resource_type']
                tenant_id = usage['tenant_id']
                amount = usage['amount']
                
                total_usage[resource_type] = total_usage.get(resource_type, 0) + amount
                
                if tenant_id not in tenant_usage:
                    tenant_usage[tenant_id] = {}
                tenant_usage[tenant_id][resource_type] = tenant_usage[tenant_id].get(resource_type, 0) + amount
            
            # Allocate shared costs proportionally
            ratios = self.shared_allocation['ratios']
            
            for tenant_id in self.tenants.keys():
                tenant_shared_cost = 0.0
                
                for resource_type, ratio in ratios.items():
                    if resource_type in total_usage and total_usage[resource_type] > 0:
                        tenant_resource_usage = tenant_usage.get(tenant_id, {}).get(resource_type, 0)
                        proportion = tenant_resource_usage / total_usage[resource_type]
                        tenant_shared_cost += total_shared_cost * ratio * proportion
                
                shared_costs[tenant_id] = tenant_shared_cost
        
        return shared_costs

    async def _store_cost_records(self, costs: Dict[str, Dict[str, float]], 
                                start_time: datetime, end_time: datetime):
        """Store calculated cost records in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for tenant_id, tenant_costs in costs.items():
            for resource_type, cost_amount in tenant_costs.items():
                if resource_type != 'total':  # Don't store total as separate record
                    cursor.execute('''
                        INSERT INTO cost_records 
                        (tenant_id, resource_type, usage_amount, cost_amount, 
                         currency, period_start, period_end, pricing_model)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tenant_id,
                        resource_type,
                        0.0,  # We don't store usage amount in cost records for now
                        cost_amount,
                        'USD',
                        start_time.isoformat(),
                        end_time.isoformat(),
                        self.shared_allocation['method']
                    ))
        
        conn.commit()
        conn.close()

    async def get_tenant_costs(self, tenant_id: str, start_time: datetime, 
                             end_time: datetime) -> Dict[str, Any]:
        """Get detailed cost breakdown for a specific tenant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT resource_type, SUM(cost_amount) as total_cost
            FROM cost_records
            WHERE tenant_id = ? AND period_start >= ? AND period_end <= ?
            GROUP BY resource_type
        ''', (tenant_id, start_time.isoformat(), end_time.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        cost_breakdown = {}
        total_cost = 0.0
        
        for row in rows:
            resource_type, cost = row
            cost_breakdown[resource_type] = cost
            total_cost += cost
        
        # Get budget information
        budget_info = self.tenants.get(tenant_id, {})
        monthly_budget = budget_info.get('budget_monthly', 0.0)
        alert_threshold = budget_info.get('alert_threshold', 0.9)
        
        # Calculate utilization
        utilization = (total_cost / monthly_budget) if monthly_budget > 0 else 0.0
        
        return {
            'tenant_id': tenant_id,
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'cost_breakdown': cost_breakdown,
            'total_cost': total_cost,
            'budget': {
                'monthly_budget': monthly_budget,
                'utilization': utilization,
                'alert_threshold': alert_threshold,
                'over_threshold': utilization > alert_threshold
            }
        }

    async def get_realtime_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get real-time usage metrics from Redis"""
        current_hour = datetime.now().strftime('%Y%m%d%H')
        current_day = datetime.now().strftime('%Y%m%d')
        
        usage_data = {}
        
        for resource_type in self.pricing_models.keys():
            hour_key = f"usage:{tenant_id}:{resource_type}:hour:{current_hour}"
            day_key = f"usage:{tenant_id}:{resource_type}:day:{current_day}"
            
            hour_usage = self.redis_client.get(hour_key)
            day_usage = self.redis_client.get(day_key)
            
            usage_data[resource_type] = {
                'hour': float(hour_usage) if hour_usage else 0.0,
                'day': float(day_usage) if day_usage else 0.0
            }
        
        return usage_data
