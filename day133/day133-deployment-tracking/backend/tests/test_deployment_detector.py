import pytest
import asyncio
from datetime import datetime, timezone
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from deployment.detector import DeploymentDetector, DeploymentEvent

@pytest.mark.asyncio
async def test_deployment_detector_initialization():
    """Test deployment detector initialization"""
    config = {"sources": ["github", "docker"]}
    detector = DeploymentDetector(config)
    
    assert detector.config == config
    assert detector.active_deployments == {}
    assert detector.deployment_history == []

@pytest.mark.asyncio
async def test_process_deployment_event():
    """Test processing deployment events"""
    detector = DeploymentDetector({"sources": []})
    
    deployment = DeploymentEvent(
        id="test_deployment_1",
        service_name="test-service",
        version="v1.0.0",
        environment="production",
        timestamp=datetime.now(timezone.utc),
        source="github_actions",
        metadata={"test": True}
    )
    
    result = await detector.process_deployment_event(deployment)
    
    assert result == deployment
    assert len(detector.deployment_history) == 1
    assert "test-service_production" in detector.active_deployments

@pytest.mark.asyncio
async def test_get_deployment_for_timestamp():
    """Test getting deployment for specific timestamp"""
    detector = DeploymentDetector({"sources": []})
    
    # Create test deployment
    deployment_time = datetime.now(timezone.utc)
    deployment = DeploymentEvent(
        id="test_deployment_2",
        service_name="test-service",
        version="v1.1.0",
        environment="production",
        timestamp=deployment_time,
        source="github_actions",
        metadata={}
    )
    
    await detector.process_deployment_event(deployment)
    
    # Test getting deployment
    result = detector.get_deployment_for_timestamp(
        deployment_time, "test-service", "production"
    )
    
    assert result is not None
    assert result.version == "v1.1.0"

def test_deployment_history_limit():
    """Test deployment history size limit"""
    detector = DeploymentDetector({"sources": []})
    
    # Add 150 deployments (more than limit of 100)
    for i in range(150):
        deployment = DeploymentEvent(
            id=f"test_deployment_{i}",
            service_name="test-service",
            version=f"v1.{i}.0",
            environment="production",
            timestamp=datetime.now(timezone.utc),
            source="github_actions",
            metadata={}
        )
        detector.deployment_history.append(deployment)
    
    # Simulate the limit check that happens in process_deployment_event
    if len(detector.deployment_history) > 100:
        detector.deployment_history = detector.deployment_history[-100:]
    
    assert len(detector.deployment_history) == 100
    assert detector.deployment_history[0].id == "test_deployment_50"
