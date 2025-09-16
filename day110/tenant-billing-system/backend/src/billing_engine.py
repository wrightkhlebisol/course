import sqlite3
from datetime import datetime, timedelta, date
from typing import Dict, List
from models import BillingCalculation, PricingTier
from usage_collector import UsageCollector

class BillingEngine:
    def __init__(self, db_path: str = "usage.db"):
        self.db_path = db_path
        self.usage_collector = UsageCollector(db_path)
        self.pricing_tiers = self._load_pricing_tiers()
        
    def _load_pricing_tiers(self) -> Dict:
        """Load pricing configuration for different tiers"""
        return {
            PricingTier.STARTER: {
                'ingestion_per_gb': 0.50,      # $0.50 per GB
                'storage_per_gb_month': 0.10,  # $0.10 per GB per month
                'query_per_1k': 0.05,          # $0.05 per 1000 queries
                'compute_per_hour': 1.00,      # $1.00 per compute hour
                'bandwidth_per_gb': 0.12,      # $0.12 per GB bandwidth
                'free_tier_gb': 1.0,           # 1GB free per month
            },
            PricingTier.PROFESSIONAL: {
                'ingestion_per_gb': 0.35,
                'storage_per_gb_month': 0.08,
                'query_per_1k': 0.03,
                'compute_per_hour': 0.80,
                'bandwidth_per_gb': 0.10,
                'free_tier_gb': 5.0,
            },
            PricingTier.ENTERPRISE: {
                'ingestion_per_gb': 0.25,
                'storage_per_gb_month': 0.06,
                'query_per_1k': 0.02,
                'compute_per_hour': 0.60,
                'bandwidth_per_gb': 0.08,
                'free_tier_gb': 50.0,
            }
        }
        
    def get_tenant_tier(self, tenant_id: str) -> PricingTier:
        """Get pricing tier for a tenant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT tier FROM tenants WHERE id = ?', (tenant_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return PricingTier(result[0])
        return PricingTier.STARTER
        
    def calculate_billing(self, tenant_id: str, start_date: date, 
                         end_date: date) -> BillingCalculation:
        """Calculate billing for a tenant over a date period"""
        
        # Get usage data
        usage_data = self.usage_collector.get_usage_for_period(
            tenant_id,
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
        
        # Aggregate usage metrics
        total_bytes = sum(row['bytes_ingested'] for row in usage_data)
        max_storage = max((row['storage_used'] for row in usage_data), default=0)
        total_queries = sum(row['queries_processed'] for row in usage_data)
        total_compute = sum(row['compute_seconds'] for row in usage_data)
        total_bandwidth = sum(row['bandwidth_gb'] for row in usage_data)
        
        # Get pricing tier
        tier = self.get_tenant_tier(tenant_id)
        pricing = self.pricing_tiers[tier]
        
        # Calculate costs
        ingestion_gb = total_bytes / (1024**3)  # Convert to GB
        storage_gb = max_storage / (1024**3)
        compute_hours = total_compute / 3600.0  # Convert to hours
        
        # Apply free tier
        billable_ingestion = max(0, ingestion_gb - pricing['free_tier_gb'])
        
        ingestion_cost = billable_ingestion * pricing['ingestion_per_gb']
        storage_cost = storage_gb * pricing['storage_per_gb_month']
        query_cost = (total_queries / 1000.0) * pricing['query_per_1k']
        compute_cost = compute_hours * pricing['compute_per_hour']
        bandwidth_cost = total_bandwidth * pricing['bandwidth_per_gb']
        
        total_cost = (ingestion_cost + storage_cost + query_cost + 
                     compute_cost + bandwidth_cost)
        
        return BillingCalculation(
            tenant_id=tenant_id,
            billing_period=f"{start_date} to {end_date}",
            total_bytes=total_bytes,
            total_storage=max_storage,
            total_queries=total_queries,
            total_compute=total_compute,
            total_bandwidth=total_bandwidth,
            ingestion_cost=round(ingestion_cost, 4),
            storage_cost=round(storage_cost, 4),
            query_cost=round(query_cost, 4),
            compute_cost=round(compute_cost, 4),
            bandwidth_cost=round(bandwidth_cost, 4),
            total_cost=round(total_cost, 2),
            tier=tier
        )
        
    def get_monthly_billing_summary(self, tenant_id: str, 
                                   month: int, year: int) -> Dict:
        """Get comprehensive billing summary for a month"""
        start_date = date(year, month, 1)
        
        # Get last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        billing = self.calculate_billing(tenant_id, start_date, end_date)
        
        # Get daily breakdown
        daily_costs = []
        current_date = start_date
        while current_date <= end_date:
            daily_billing = self.calculate_billing(tenant_id, current_date, current_date)
            daily_costs.append({
                'date': current_date.isoformat(),
                'cost': daily_billing.total_cost
            })
            current_date += timedelta(days=1)
            
        return {
            'billing_summary': billing.dict(),
            'daily_breakdown': daily_costs,
            'cost_trend': self._calculate_cost_trend(daily_costs)
        }
        
    def _calculate_cost_trend(self, daily_costs: List[Dict]) -> str:
        """Calculate cost trend direction"""
        if len(daily_costs) < 7:
            return "insufficient_data"
            
        recent_avg = sum(day['cost'] for day in daily_costs[-7:]) / 7
        previous_avg = sum(day['cost'] for day in daily_costs[-14:-7]) / 7
        
        if recent_avg > previous_avg * 1.1:
            return "increasing"
        elif recent_avg < previous_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
