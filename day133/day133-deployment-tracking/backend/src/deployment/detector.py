import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import aiofiles
import requests
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger()

@dataclass
class DeploymentEvent:
    id: str
    service_name: str
    version: str
    environment: str
    timestamp: datetime
    source: str
    metadata: Dict
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    
class DeploymentDetector:
    def __init__(self, config: Dict):
        self.config = config
        self.active_deployments = {}
        self.deployment_history = []
        
    async def start_monitoring(self):
        """Start monitoring deployment sources"""
        logger.info("Starting deployment monitoring")
        
        # Start monitoring tasks
        tasks = [
            self.monitor_github_actions(),
            self.monitor_docker_registry(),
            self.monitor_kubernetes(),
            self.generate_demo_deployments()  # For demo purposes
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def monitor_github_actions(self):
        """Monitor GitHub Actions for deployment events"""
        while True:
            try:
                # In production, this would connect to GitHub webhooks
                await asyncio.sleep(30)
                logger.debug("Monitoring GitHub Actions...")
            except Exception as e:
                logger.error(f"GitHub Actions monitoring error: {e}")
            
    async def monitor_docker_registry(self):
        """Monitor Docker registry for new image pushes"""
        while True:
            try:
                # In production, this would connect to registry webhooks
                await asyncio.sleep(25)
                logger.debug("Monitoring Docker registry...")
            except Exception as e:
                logger.error(f"Docker registry monitoring error: {e}")
            
    async def monitor_kubernetes(self):
        """Monitor Kubernetes deployments"""
        while True:
            try:
                # In production, this would use Kubernetes API
                await asyncio.sleep(35)
                logger.debug("Monitoring Kubernetes deployments...")
            except Exception as e:
                logger.error(f"Kubernetes monitoring error: {e}")
                
    async def generate_demo_deployments(self):
        """Generate demo deployment events for demonstration"""
        services = ["user-service", "payment-service", "notification-service", "api-gateway"]
        environments = ["staging", "production"]
        
        while True:
            try:
                import random
                service = random.choice(services)
                env = random.choice(environments)
                version = f"v{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}"
                
                deployment = DeploymentEvent(
                    id=f"dep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{service}",
                    service_name=service,
                    version=version,
                    environment=env,
                    timestamp=datetime.now(timezone.utc),
                    source="github_actions",
                    metadata={
                        "triggered_by": "user@company.com",
                        "duration": random.randint(60, 300),
                        "deployment_type": "rolling_update"
                    },
                    commit_hash=f"abc{random.randint(1000,9999)}def",
                    branch="main"
                )
                
                await self.process_deployment_event(deployment)
                
                # Random interval between 30 seconds to 2 minutes
                await asyncio.sleep(random.randint(30, 120))
                
            except Exception as e:
                logger.error(f"Demo deployment generation error: {e}")
                await asyncio.sleep(10)
    
    async def process_deployment_event(self, deployment: DeploymentEvent):
        """Process a new deployment event"""
        key = f"{deployment.service_name}_{deployment.environment}"
        self.active_deployments[key] = deployment
        self.deployment_history.append(deployment)
        
        # Keep only last 100 deployments in memory
        if len(self.deployment_history) > 100:
            self.deployment_history = self.deployment_history[-100:]
        
        logger.info(f"New deployment detected: {deployment.service_name} {deployment.version}")
        
        # Save to file for persistence
        await self.save_deployment_data()
        
        return deployment
    
    async def save_deployment_data(self):
        """Save deployment data to file"""
        try:
            data = {
                'active_deployments': {k: asdict(v) for k, v in self.active_deployments.items()},
                'history': [asdict(d) for d in self.deployment_history[-50:]]  # Save last 50
            }
            
            async with aiofiles.open('data/deployments.json', 'w') as f:
                await f.write(json.dumps(data, default=str, indent=2))
                
        except Exception as e:
            logger.error(f"Error saving deployment data: {e}")
    
    def get_active_deployments(self) -> Dict:
        """Get currently active deployments"""
        return {k: asdict(v) for k, v in self.active_deployments.items()}
    
    def get_deployment_history(self) -> List[Dict]:
        """Get deployment history"""
        return [asdict(d) for d in self.deployment_history]
    
    def get_deployment_for_timestamp(self, timestamp: datetime, service: str, environment: str) -> Optional[DeploymentEvent]:
        """Get deployment active at a specific timestamp"""
        key = f"{service}_{environment}"
        
        # Find the most recent deployment before the timestamp
        relevant_deployments = [
            d for d in self.deployment_history 
            if d.service_name == service and d.environment == environment and d.timestamp <= timestamp
        ]
        
        if relevant_deployments:
            return max(relevant_deployments, key=lambda x: x.timestamp)
        
        return None
