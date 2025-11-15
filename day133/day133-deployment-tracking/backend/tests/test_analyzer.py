import pytest
import asyncio
from datetime import datetime, timezone
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from analysis.analyzer import ImpactAnalyzer
from deployment.detector import DeploymentDetector, DeploymentEvent

@pytest.mark.asyncio
async def test_impact_calculation():
    """Test impact calculation logic"""
    detector = DeploymentDetector({"sources": []})
    analyzer = ImpactAnalyzer(detector)
    
    # Test metrics with significant changes
    before_metrics = {
        "response_time_avg": 100,
        "error_rate": 0.01,
        "throughput": 1000
    }
    
    after_metrics = {
        "response_time_avg": 150,  # 50% increase
        "error_rate": 0.02,        # 100% increase
        "throughput": 950          # 5% decrease
    }
    
    impact_score, significant_changes = analyzer.calculate_impact(before_metrics, after_metrics)
    
    assert impact_score > 0
    assert len(significant_changes) > 0
    assert any("response_time_avg" in change for change in significant_changes)

@pytest.mark.asyncio
async def test_deployment_impact_analysis():
    """Test deployment impact analysis"""
    detector = DeploymentDetector({"sources": []})
    analyzer = ImpactAnalyzer(detector)
    
    # Create test deployment
    deployment = DeploymentEvent(
        id="test_deployment_impact",
        service_name="test-service",
        version="v1.5.0",
        environment="production",
        timestamp=datetime.now(timezone.utc),
        source="github_actions",
        metadata={}
    )
    
    # Analyze impact
    impact = await analyzer.analyze_deployment_impact(deployment)
    
    assert impact is not None
    assert impact.deployment_id == "test_deployment_impact"
    assert impact.service_name == "test-service"
    assert impact.version == "v1.5.0"
    assert "before_metrics" in impact.__dict__
    assert "after_metrics" in impact.__dict__

def test_impact_summary():
    """Test impact summary generation"""
    detector = DeploymentDetector({"sources": []})
    analyzer = ImpactAnalyzer(detector)
    
    # Test with no impact results
    summary = analyzer.get_impact_summary()
    assert summary["total_analyzed"] == 0
    
    # TODO: Add test with mock impact results
