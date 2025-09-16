from datetime import datetime, date
from typing import Dict, Tuple
from models import PricingTier, TenantQuota
from usage_collector import UsageCollector
import sqlite3

class QuotaEnforcer:
    def __init__(self, db_path: str = "usage.db"):
        self.db_path = db_path
        self.usage_collector = UsageCollector(db_path)
        self.quota_limits = self._load_quota_limits()
        
    def _load_quota_limits(self) -> Dict:
        """Load quota limits for different tiers"""
        return {
            PricingTier.STARTER: {
                'daily_ingestion_gb': 5.0,
                'storage_gb': 10.0,
                'daily_queries': 1000,
                'concurrent_queries': 5
            },
            PricingTier.PROFESSIONAL: {
                'daily_ingestion_gb': 50.0,
                'storage_gb': 500.0,
                'daily_queries': 10000,
                'concurrent_queries': 20
            },
            PricingTier.ENTERPRISE: {
                'daily_ingestion_gb': 1000.0,
                'storage_gb': 5000.0,
                'daily_queries': 100000,
                'concurrent_queries': 100
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
        
    def check_ingestion_quota(self, tenant_id: str, bytes_to_ingest: int) -> Tuple[bool, Dict]:
        """Check if tenant can ingest specified bytes without exceeding quota"""
        tier = self.get_tenant_tier(tenant_id)
        limits = self.quota_limits[tier]
        
        # Get current daily usage
        today = date.today()
        current_usage = self.usage_collector.get_current_usage(tenant_id)
        
        current_bytes = current_usage.get('daily_bytes_ingested', 0)
        current_gb = current_bytes / (1024**3)
        new_bytes_gb = bytes_to_ingest / (1024**3)
        
        total_gb_after_ingest = current_gb + new_bytes_gb
        daily_limit_gb = limits['daily_ingestion_gb']
        
        within_quota = total_gb_after_ingest <= daily_limit_gb
        
        quota_info = {
            'tenant_id': tenant_id,
            'tier': tier.value,
            'current_usage_gb': round(current_gb, 4),
            'requested_gb': round(new_bytes_gb, 4),
            'total_after_request_gb': round(total_gb_after_ingest, 4),
            'daily_limit_gb': daily_limit_gb,
            'remaining_quota_gb': max(0, daily_limit_gb - current_gb),
            'quota_utilization_percent': round((current_gb / daily_limit_gb) * 100, 2),
            'within_quota': within_quota,
            'checked_at': datetime.now().isoformat()
        }
        
        return within_quota, quota_info
        
    def check_query_quota(self, tenant_id: str) -> Tuple[bool, Dict]:
        """Check if tenant can execute another query"""
        tier = self.get_tenant_tier(tenant_id)
        limits = self.quota_limits[tier]
        
        current_usage = self.usage_collector.get_current_usage(tenant_id)
        daily_queries = current_usage.get('daily_queries_processed', 0)
        daily_limit = limits['daily_queries']
        
        within_quota = daily_queries < daily_limit
        
        quota_info = {
            'tenant_id': tenant_id,
            'tier': tier.value,
            'daily_queries_used': daily_queries,
            'daily_query_limit': daily_limit,
            'remaining_queries': max(0, daily_limit - daily_queries),
            'quota_utilization_percent': round((daily_queries / daily_limit) * 100, 2),
            'within_quota': within_quota,
            'checked_at': datetime.now().isoformat()
        }
        
        return within_quota, quota_info
        
    def get_tenant_quota_status(self, tenant_id: str) -> TenantQuota:
        """Get complete quota status for a tenant"""
        tier = self.get_tenant_tier(tenant_id)
        limits = self.quota_limits[tier]
        current_usage = self.usage_collector.get_current_usage(tenant_id)
        
        return TenantQuota(
            tenant_id=tenant_id,
            tier=tier,
            daily_ingestion_limit=int(limits['daily_ingestion_gb'] * (1024**3)),
            storage_limit=int(limits['storage_gb'] * (1024**3)),
            query_limit=limits['daily_queries'],
            current_usage={
                'daily_bytes_ingested': current_usage.get('daily_bytes_ingested', 0),
                'current_storage_used': current_usage.get('current_storage_used', 0),
                'daily_queries_processed': current_usage.get('daily_queries_processed', 0),
                'last_updated': current_usage.get('last_updated')
            }
        )
        
    def enforce_rate_limit(self, tenant_id: str, operation: str) -> Tuple[bool, str]:
        """Enforce rate limits for different operations"""
        tier = self.get_tenant_tier(tenant_id)
        
        if operation == "ingestion":
            # Check recent ingestion rate (simple implementation)
            recent_usage = self.usage_collector.get_current_usage(tenant_id)
            data_points = recent_usage.get('data_points', 0)
            
            # Allow max 100 data points per minute for starter
            max_rate = 100 if tier == PricingTier.STARTER else 1000
            
            if data_points > max_rate:
                return False, f"Rate limit exceeded: {data_points} > {max_rate} operations/minute"
                
        elif operation == "query":
            within_quota, quota_info = self.check_query_quota(tenant_id)
            if not within_quota:
                return False, f"Daily query quota exceeded: {quota_info['daily_queries_used']}"
                
        return True, "Within rate limits"
