import pytest
import asyncio
import sqlite3
from datetime import datetime, timedelta
import tempfile
import os
import yaml

# Import components to test
import sys
sys.path.append('src')

from cost_engine.core import CostEngine, ResourceUsage

@pytest.fixture
def test_config():
    import tempfile
    import os
    # Create a temporary database file for tests
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    return {
        'database': {
            'path': temp_db.name  # Use temporary file database for tests
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 1  # Use different DB for tests
        },
        'cost_allocation': {
            'pricing_models': {
                'ingestion': {'price_per_gb': 0.10},
                'storage': {'price_per_gb_month': 0.05},
                'queries': {'price_per_query': 0.001},
                'compute': {'price_per_cpu_hour': 0.02}
            },
            'shared_allocation': {
                'method': 'proportional',
                'ratios': {
                    'ingestion': 0.5,
                    'storage': 0.3,
                    'queries': 0.2
                }
            },
            'tenants': {
                'test_tenant': {
                    'budget_monthly': 1000.0,
                    'alert_threshold': 0.9
                }
            }
        }
    }

@pytest.fixture
def cost_engine(test_config):
    engine = CostEngine(test_config)
    # Ensure database is initialized
    engine._init_database()
    yield engine
    # Cleanup: remove temporary database file
    import os
    if os.path.exists(engine.db_path):
        os.unlink(engine.db_path)

@pytest.mark.asyncio
async def test_track_usage(cost_engine):
    """Test usage tracking functionality"""
    usage = ResourceUsage(
        tenant_id='test_tenant',
        resource_type='ingestion',
        amount=10.0,
        unit='GB',
        timestamp=datetime.now(),
        metadata={'source': 'test'}
    )
    
    result = await cost_engine.track_usage(usage)
    assert result == True

@pytest.mark.asyncio
async def test_calculate_costs(cost_engine):
    """Test cost calculation"""
    # Track some usage first
    usage = ResourceUsage(
        tenant_id='test_tenant',
        resource_type='ingestion',
        amount=10.0,
        unit='GB',
        timestamp=datetime.now(),
        metadata={}
    )
    
    await cost_engine.track_usage(usage)
    
    # Calculate costs
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now() + timedelta(hours=1)
    
    costs = await cost_engine.calculate_costs(start_time, end_time)
    
    assert 'test_tenant' in costs
    assert costs['test_tenant']['ingestion'] == 1.0  # 10 GB * $0.10

@pytest.mark.asyncio
async def test_get_tenant_costs(cost_engine):
    """Test tenant cost retrieval"""
    # Track usage and calculate costs
    usage = ResourceUsage(
        tenant_id='test_tenant',
        resource_type='storage',
        amount=100.0,
        unit='GB',
        timestamp=datetime.now(),
        metadata={}
    )
    
    await cost_engine.track_usage(usage)
    
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now() + timedelta(hours=1)
    
    await cost_engine.calculate_costs(start_time, end_time)
    
    tenant_costs = await cost_engine.get_tenant_costs('test_tenant', start_time, end_time)
    
    assert tenant_costs['tenant_id'] == 'test_tenant'
    assert 'cost_breakdown' in tenant_costs
    assert 'budget' in tenant_costs

@pytest.mark.asyncio
async def test_realtime_usage(cost_engine):
    """Test real-time usage tracking"""
    usage = ResourceUsage(
        tenant_id='test_tenant',
        resource_type='queries',
        amount=100.0,
        unit='queries',
        timestamp=datetime.now(),
        metadata={}
    )
    
    await cost_engine.track_usage(usage)
    
    realtime_data = await cost_engine.get_realtime_usage('test_tenant')
    
    assert 'queries' in realtime_data
    assert realtime_data['queries']['hour'] >= 0
    assert realtime_data['queries']['day'] >= 0

def test_database_initialization(cost_engine):
    """Test database table creation"""
    conn = sqlite3.connect(cost_engine.db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert 'usage_records' in tables
    assert 'cost_records' in tables
    
    conn.close()
