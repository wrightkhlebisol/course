import asyncio
import json
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class ImpactMetrics:
    deployment_id: str
    service_name: str
    version: str
    before_metrics: Dict
    after_metrics: Dict
    impact_score: float
    significant_changes: List[str]
    analysis_timestamp: datetime

class ImpactAnalyzer:
    def __init__(self, deployment_detector):
        self.deployment_detector = deployment_detector
        self.metrics_cache = {}
        self.impact_results = []
        
    async def start_analysis(self):
        """Start continuous impact analysis"""
        logger.info("Starting deployment impact analysis")
        
        while True:
            try:
                await self.analyze_recent_deployments()
                await asyncio.sleep(60)  # Analyze every minute
            except Exception as e:
                logger.error(f"Impact analysis error: {e}")
                await asyncio.sleep(10)
    
    async def analyze_recent_deployments(self):
        """Analyze impact of recent deployments"""
        recent_deployments = [
            d for d in self.deployment_detector.deployment_history
            if (datetime.now(timezone.utc) - d.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        for deployment in recent_deployments:
            if not any(r.deployment_id == deployment.id for r in self.impact_results):
                impact = await self.analyze_deployment_impact(deployment)
                if impact:
                    self.impact_results.append(impact)
                    
                    # Keep only last 50 results
                    if len(self.impact_results) > 50:
                        self.impact_results = self.impact_results[-50:]
    
    async def analyze_deployment_impact(self, deployment) -> Optional[ImpactMetrics]:
        """Analyze impact of a specific deployment"""
        try:
            # Define time windows for before/after analysis
            deployment_time = deployment.timestamp
            before_start = deployment_time - timedelta(minutes=30)
            before_end = deployment_time
            after_start = deployment_time
            after_end = deployment_time + timedelta(minutes=30)
            
            # Generate synthetic metrics for demo
            before_metrics = await self.generate_metrics(before_start, before_end, deployment.service_name)
            after_metrics = await self.generate_metrics(after_start, after_end, deployment.service_name)
            
            # Calculate impact score and significant changes
            impact_score, significant_changes = self.calculate_impact(before_metrics, after_metrics)
            
            impact = ImpactMetrics(
                deployment_id=deployment.id,
                service_name=deployment.service_name,
                version=deployment.version,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                impact_score=impact_score,
                significant_changes=significant_changes,
                analysis_timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"Deployment impact analyzed: {deployment.service_name} - Score: {impact_score:.2f}")
            return impact
            
        except Exception as e:
            logger.error(f"Error analyzing deployment impact: {e}")
            return None
    
    async def generate_metrics(self, start_time: datetime, end_time: datetime, service: str) -> Dict:
        """Generate synthetic metrics for demo purposes"""
        import random
        
        # Base metrics that vary by service
        base_metrics = {
            "user-service": {"response_time": 150, "error_rate": 0.02, "throughput": 1000},
            "payment-service": {"response_time": 300, "error_rate": 0.01, "throughput": 500},
            "notification-service": {"response_time": 100, "error_rate": 0.05, "throughput": 2000},
            "api-gateway": {"response_time": 50, "error_rate": 0.03, "throughput": 5000}
        }
        
        base = base_metrics.get(service, {"response_time": 200, "error_rate": 0.03, "throughput": 1000})
        
        # Add some randomness
        metrics = {
            "response_time_avg": base["response_time"] + random.uniform(-20, 20),
            "response_time_p95": base["response_time"] * 1.5 + random.uniform(-30, 30),
            "error_rate": max(0, base["error_rate"] + random.uniform(-0.01, 0.01)),
            "throughput": base["throughput"] + random.uniform(-100, 100),
            "cpu_usage": random.uniform(30, 80),
            "memory_usage": random.uniform(40, 85),
            "success_rate": 1 - base["error_rate"] + random.uniform(-0.02, 0.02)
        }
        
        return metrics
    
    def calculate_impact(self, before: Dict, after: Dict) -> tuple:
        """Calculate impact score and identify significant changes"""
        significant_changes = []
        total_impact = 0
        
        # Define thresholds for significant changes
        thresholds = {
            "response_time_avg": 0.15,  # 15% change
            "response_time_p95": 0.20,  # 20% change
            "error_rate": 0.5,          # 50% change
            "throughput": 0.10,         # 10% change
            "cpu_usage": 0.20,          # 20% change
            "memory_usage": 0.20,       # 20% change
            "success_rate": 0.02        # 2% change
        }
        
        for metric in before.keys():
            if metric in after and metric in thresholds:
                before_val = before[metric]
                after_val = after[metric]
                
                if before_val != 0:
                    change_ratio = abs(after_val - before_val) / before_val
                    
                    if change_ratio > thresholds[metric]:
                        direction = "increased" if after_val > before_val else "decreased"
                        percentage = change_ratio * 100
                        significant_changes.append(f"{metric} {direction} by {percentage:.1f}%")
                        
                        # Weight impact based on metric importance
                        weights = {
                            "error_rate": 3.0,
                            "response_time_avg": 2.0,
                            "response_time_p95": 2.0,
                            "success_rate": 3.0,
                            "throughput": 1.5,
                            "cpu_usage": 1.0,
                            "memory_usage": 1.0
                        }
                        
                        weight = weights.get(metric, 1.0)
                        total_impact += change_ratio * weight
        
        # Normalize impact score to 0-100 scale
        impact_score = min(100, total_impact * 100)
        
        return impact_score, significant_changes
    
    def get_impact_summary(self) -> Dict:
        """Get summary of deployment impacts"""
        if not self.impact_results:
            return {"total_analyzed": 0}
        
        return {
            "total_analyzed": len(self.impact_results),
            "high_impact_deployments": len([r for r in self.impact_results if r.impact_score > 50]),
            "average_impact_score": np.mean([r.impact_score for r in self.impact_results]),
            "recent_impacts": [
                {
                    "deployment_id": r.deployment_id,
                    "service": r.service_name,
                    "version": r.version,
                    "impact_score": r.impact_score,
                    "significant_changes": r.significant_changes
                }
                for r in self.impact_results[-10:]  # Last 10 impacts
            ]
        }
