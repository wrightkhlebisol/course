import pytest
import asyncio
import tempfile
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.models import Base, LogEntry, PolicyRule
from src.backend.policy_engine.engine import PolicyEngine

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

@pytest.fixture
def policy_engine(temp_db):
    """Create policy engine instance for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test config files
        storage_config = {
            "hot": {"path": f"{tmpdir}/hot", "max_age_days": 1, "cost_per_gb": 0.25},
            "warm": {"path": f"{tmpdir}/warm", "max_age_days": 7, "cost_per_gb": 0.10}
        }
        
        config_file = f"{tmpdir}/storage_tiers.json"
        with open(config_file, 'w') as f:
            json.dump(storage_config, f)
        
        engine = PolicyEngine()
        engine.storage_config = storage_config
        yield engine

def test_policy_evaluation(policy_engine):
    """Test policy evaluation logic"""
    # Create test log entry
    log_entry = LogEntry(
        log_id="test_log_001",
        log_type="customer_activity",
        current_tier="hot",
        file_path="/test/path",
        file_size_bytes=1024,
        created_at=datetime.utcnow() - timedelta(days=2)  # 2 days old
    )
    
    # Create test policy
    policy = PolicyRule(
        name="test_policy",
        log_type="customer_activity",
        rule_type="time_based",
        conditions={"hot_max_hours": 24},  # 1 day max in hot
        action="move_to_warm"
    )
    
    # Test evaluation
    action = policy_engine._evaluate_log_against_policy(log_entry, policy)
    assert action == "move_to_warm"

def test_cost_calculation(policy_engine):
    """Test cost impact calculation"""
    log_entry = LogEntry(
        log_id="test_log_002",
        log_type="debug_logs",
        current_tier="hot",
        file_path="/test/path",
        file_size_bytes=1024*1024*1024,  # 1GB
        created_at=datetime.utcnow()
    )
    
    cost_impact = policy_engine._calculate_cost_impact(log_entry, "move_to_warm")
    expected_savings = 1.0 * (0.25 - 0.10)  # 1GB * (hot_cost - warm_cost)
    assert abs(cost_impact - expected_savings) < 0.01

@pytest.mark.asyncio
async def test_policy_engine_startup():
    """Test policy engine can start and stop"""
    engine = PolicyEngine()
    
    # Start engine in background
    task = asyncio.create_task(engine.start())
    
    # Let it run briefly
    await asyncio.sleep(0.1)
    
    # Stop engine
    engine.stop()
    task.cancel()
    
    assert not engine.running
