import pytest
import sqlite3
import os
from datetime import datetime, date, timedelta
from src.usage_collector import UsageCollector
from src.billing_engine import BillingEngine
from src.report_generator import ReportGenerator
from src.quota_enforcer import QuotaEnforcer
from src.models import UsageMetric, PricingTier

@pytest.fixture
def test_db():
    """Create a test database"""
    db_path = "test_usage.db"
    # Clean up if exists
    if os.path.exists(db_path):
        os.remove(db_path)
    yield db_path
    # Clean up after test
    if os.path.exists(db_path):
        os.remove(db_path)

def test_usage_collector(test_db):
    """Test usage collection functionality"""
    collector = UsageCollector(test_db)
    
    # Test recording usage
    usage = UsageMetric(
        tenant_id="test_tenant",
        timestamp=datetime.now(),
        bytes_ingested=1000000,  # 1MB
        storage_used=5000000,    # 5MB
        queries_processed=100,
        compute_seconds=10.5,
        bandwidth_gb=0.1
    )
    
    result = collector.record_usage(usage)
    assert result == True
    
    # Test retrieving current usage
    current = collector.get_current_usage("test_tenant")
    assert current['tenant_id'] == "test_tenant"
    assert current['daily_bytes_ingested'] >= 1000000

def test_billing_engine(test_db):
    """Test billing calculations"""
    collector = UsageCollector(test_db)
    billing_engine = BillingEngine(test_db)
    
    # Add test tenant
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tenants (id, name, tier) VALUES (?, ?, ?)',
                  ('test_tenant', 'Test Corp', 'professional'))
    conn.commit()
    conn.close()
    
    # Add some usage data
    today = date.today()
    usage = UsageMetric(
        tenant_id="test_tenant",
        timestamp=datetime.now(),
        bytes_ingested=10000000000,  # 10GB (exceeds 5GB free tier)
        storage_used=1000000000,     # 1GB
        queries_processed=5000,
        compute_seconds=3600,        # 1 hour
        bandwidth_gb=0.5
    )
    collector.record_usage(usage)
    
    # Test billing calculation
    billing = billing_engine.calculate_billing("test_tenant", today, today)
    
    assert billing.tenant_id == "test_tenant"
    assert billing.tier == PricingTier.PROFESSIONAL
    assert billing.total_cost > 0
    assert billing.ingestion_cost > 0
    assert billing.compute_cost > 0

def test_quota_enforcer(test_db):
    """Test quota enforcement"""
    collector = UsageCollector(test_db)
    quota_enforcer = QuotaEnforcer(test_db)
    
    # Add test tenant
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tenants (id, name, tier) VALUES (?, ?, ?)',
                  ('test_tenant', 'Test Corp', 'starter'))
    conn.commit()
    conn.close()
    
    # Test ingestion quota check
    bytes_to_ingest = 1000000000  # 1GB
    within_quota, quota_info = quota_enforcer.check_ingestion_quota("test_tenant", bytes_to_ingest)
    
    assert isinstance(within_quota, bool)
    assert 'tenant_id' in quota_info
    assert 'quota_utilization_percent' in quota_info

def test_report_generator(test_db):
    """Test report generation"""
    collector = UsageCollector(test_db)
    report_generator = ReportGenerator(test_db)
    
    # Add test tenant
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tenants (id, name, tier) VALUES (?, ?, ?)',
                  ('test_tenant', 'Test Corp', 'enterprise'))
    conn.commit()
    conn.close()
    
    # Add usage data
    usage = UsageMetric(
        tenant_id="test_tenant",
        timestamp=datetime.now(),
        bytes_ingested=1500000000,  # 1.5GB
        storage_used=800000000,     # 800MB
        queries_processed=2000,
        compute_seconds=1800,       # 30 minutes
        bandwidth_gb=0.3
    )
    collector.record_usage(usage)
    
    # Generate report
    today = date.today()
    report = report_generator.generate_usage_report("test_tenant", today, today)
    
    assert report.tenant_id == "test_tenant"
    assert report.period_start == today
    assert report.period_end == today
    assert 'total_bytes_ingested' in report.usage_summary
    assert 'total_cost' in report.cost_breakdown
    assert len(report.daily_usage) >= 1

if __name__ == "__main__":
    pytest.main(["-v"])
