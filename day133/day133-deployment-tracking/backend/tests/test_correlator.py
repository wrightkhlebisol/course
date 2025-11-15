import pytest
import asyncio
from datetime import datetime, timezone
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from correlation.correlator import VersionCorrelator
from deployment.detector import DeploymentDetector, DeploymentEvent

@pytest.mark.asyncio
async def test_log_enrichment():
    """Test log entry enrichment with deployment context"""
    # Setup
    detector = DeploymentDetector({"sources": []})
    correlator = VersionCorrelator(detector)
    
    # Create test deployment
    deployment = DeploymentEvent(
        id="test_deployment",
        service_name="test-service",
        version="v2.0.0",
        environment="production",
        timestamp=datetime.now(timezone.utc),
        source="github_actions",
        metadata={},
        commit_hash="abc123def"
    )
    
    await detector.process_deployment_event(deployment)
    
    # Test log entry
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "test-service",
        "environment": "production",
        "level": "INFO",
        "message": "Test log message"
    }
    
    # Enrich log entry
    enriched = await correlator.enrich_log_entry(log_entry)
    
    assert "deployment" in enriched
    assert enriched["deployment"]["version"] == "v2.0.0"
    assert enriched["deployment"]["commit_hash"] == "abc123def"

@pytest.mark.asyncio
async def test_batch_enrichment():
    """Test batch log enrichment"""
    detector = DeploymentDetector({"sources": []})
    correlator = VersionCorrelator(detector)
    
    # Test with multiple log entries
    log_entries = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "unknown-service",
            "message": "Test message 1"
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "unknown-service",
            "message": "Test message 2"
        }
    ]
    
    enriched_logs = await correlator.batch_enrich_logs(log_entries)
    
    assert len(enriched_logs) == 2
    assert all("deployment" in log for log in enriched_logs)

def test_correlation_stats():
    """Test correlation statistics"""
    detector = DeploymentDetector({"sources": []})
    correlator = VersionCorrelator(detector)
    
    stats = correlator.get_correlation_stats()
    
    assert "cache_size" in stats
    assert "active_deployments" in stats
    assert "total_deployments" in stats
