from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict
from enum import Enum

class PricingTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional" 
    ENTERPRISE = "enterprise"

class UsageMetric(BaseModel):
    tenant_id: str
    timestamp: datetime
    bytes_ingested: int
    storage_used: int
    queries_processed: int
    compute_seconds: float
    bandwidth_gb: float

class BillingCalculation(BaseModel):
    tenant_id: str
    billing_period: str
    total_bytes: int
    total_storage: int
    total_queries: int
    total_compute: float
    total_bandwidth: float
    ingestion_cost: float
    storage_cost: float
    query_cost: float
    compute_cost: float
    bandwidth_cost: float
    total_cost: float
    tier: PricingTier

class UsageReport(BaseModel):
    tenant_id: str
    period_start: date
    period_end: date
    usage_summary: Dict
    cost_breakdown: Dict
    daily_usage: List[Dict]
    top_services: List[Dict]

class TenantQuota(BaseModel):
    tenant_id: str
    tier: PricingTier
    daily_ingestion_limit: int
    storage_limit: int
    query_limit: int
    current_usage: Dict
