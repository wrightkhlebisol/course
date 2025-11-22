"""
Alert Router - Core component for alert classification and routing
Determines which incidents should be created in which external systems
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import structlog

logger = structlog.get_logger()

class AlertSeverity(Enum):
    """Alert severity levels mapped to external system severities"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    INFO = "info"

class AlertSource(Enum):
    """Source systems that generate alerts"""
    DATABASE = "database"
    API = "api"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"

@dataclass
class AlertData:
    """Structured alert data"""
    id: str
    title: str
    description: str
    source: AlertSource
    severity: AlertSeverity
    timestamp: datetime
    metadata: Dict[str, Any]
    tags: List[str]
    service_name: str
    team: Optional[str] = None

@dataclass
class RoutingResult:
    """Result of alert routing decision"""
    alert_id: str
    provider: str
    incident_id: Optional[str]
    escalation_policy: str
    success: bool
    error: Optional[str] = None

class AlertRouter:
    """Core alert routing and classification engine"""
    
    def __init__(self, incident_manager):
        self.incident_manager = incident_manager
        self.escalation_policies = {}
        self.service_catalog = {}
        self.routing_rules = {}
        
    async def load_escalation_policies(self):
        """Load escalation policies from configuration"""
        # Default escalation policies
        self.escalation_policies = {
            "critical_24x7": {
                "provider": "pagerduty",
                "escalation_timeout": 5,  # minutes
                "teams": ["oncall-primary", "oncall-secondary"]
            },
            "business_hours": {
                "provider": "opsgenie",
                "escalation_timeout": 15,
                "teams": ["support-team"]
            },
            "infrastructure": {
                "provider": "pagerduty", 
                "escalation_timeout": 10,
                "teams": ["infrastructure-team"]
            },
            "security": {
                "provider": "both",  # Create in both systems for security
                "escalation_timeout": 2,
                "teams": ["security-team", "oncall-primary"]
            }
        }
        
        # Service to team mapping
        self.service_catalog = {
            "payment-service": {"team": "payments", "criticality": "critical"},
            "user-service": {"team": "identity", "criticality": "high"},
            "recommendation-service": {"team": "ml", "criticality": "medium"},
            "logging-service": {"team": "infrastructure", "criticality": "low"},
            "security-service": {"team": "security", "criticality": "critical"}
        }
        
        # Routing rules based on alert characteristics
        self.routing_rules = {
            ("database", "critical"): "critical_24x7",
            ("security", "*"): "security",  # All security alerts
            ("api", "critical"): "critical_24x7",
            ("infrastructure", "*"): "infrastructure",
            ("application", "critical"): "critical_24x7",
            ("application", "high"): "business_hours",
            ("*", "low"): "business_hours",  # Default for low priority
        }
        
        logger.info("Escalation policies loaded", policies=len(self.escalation_policies))
    
    async def process_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming alert and route to appropriate system"""
        start_time = time.time()
        
        try:
            # Parse and validate alert data
            alert = self._parse_alert_data(alert_data)
            logger.info("Processing alert", alert_id=alert.id, severity=alert.severity.value)
            
            # Apply classification rules
            classified_alert = await self._classify_alert(alert)
            
            # Determine routing destination
            routing_policy = self._get_routing_policy(classified_alert)
            
            # Create incident(s) in external systems
            routing_results = await self._create_incidents(classified_alert, routing_policy)
            
            # If all external attempts failed, create a local incident
            if routing_results and not any(r.success for r in routing_results):
                local_incident_id = await self._create_local_incident(classified_alert, routing_policy)
                logger.info("Created local incident", incident_id=local_incident_id, alert_id=alert.id)
            
            processing_time = time.time() - start_time
            
            return {
                "alert_id": alert.id,
                "processing_time_ms": round(processing_time * 1000, 2),
                "routing_results": [asdict(result) for result in routing_results],
                "success": any(r.success for r in routing_results) or len(routing_results) == 0
            }
            
        except Exception as e:
            logger.error("Alert processing failed", error=str(e))
            return {
                "alert_id": alert_data.get("id", "unknown"),
                "success": False,
                "error": str(e)
            }
    
    def _parse_alert_data(self, data: Dict[str, Any]) -> AlertData:
        """Parse raw alert data into structured format"""
        return AlertData(
            id=data.get("id", f"alert_{int(time.time())}"),
            title=data.get("title", "Unknown Alert"),
            description=data.get("description", ""),
            source=AlertSource(data.get("source", "application")),
            severity=AlertSeverity(data.get("severity", "medium")),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now(timezone.utc).isoformat())
            ),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            service_name=data.get("service_name", "unknown-service"),
            team=data.get("team")
        )
    
    async def _classify_alert(self, alert: AlertData) -> AlertData:
        """Apply classification rules to enhance alert data"""
        # Enhance with service catalog information
        if alert.service_name in self.service_catalog:
            service_info = self.service_catalog[alert.service_name]
            if not alert.team:
                alert.team = service_info["team"]
            
            # Upgrade severity based on service criticality
            if service_info["criticality"] == "critical" and alert.severity in [AlertSeverity.MEDIUM, AlertSeverity.LOW]:
                alert.severity = AlertSeverity.HIGH
                alert.tags.append("service-critical")
        
        # Time-based classification
        current_hour = datetime.now().hour
        if current_hour < 8 or current_hour > 18:  # After hours
            alert.tags.append("after-hours")
        
        return alert
    
    def _get_routing_policy(self, alert: AlertData) -> str:
        """Determine which escalation policy to use"""
        # Check specific routing rules
        for (source_pattern, severity_pattern), policy in self.routing_rules.items():
            if ((source_pattern == "*" or source_pattern == alert.source.value) and
                (severity_pattern == "*" or severity_pattern == alert.severity.value)):
                return policy
        
        # Default routing based on severity
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return "critical_24x7"
        else:
            return "business_hours"
    
    async def _create_incidents(self, alert: AlertData, policy_name: str) -> List[RoutingResult]:
        """Create incident(s) in external systems based on policy"""
        policy = self.escalation_policies[policy_name]
        results = []
        
        providers = []
        if policy["provider"] == "both":
            providers = ["pagerduty", "opsgenie"]
        else:
            providers = [policy["provider"]]
        
        # Create incidents in parallel
        tasks = []
        for provider in providers:
            task = self._create_provider_incident(alert, provider, policy, policy_name)
            tasks.append(task)
        
        incident_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(incident_results):
            if isinstance(result, Exception):
                results.append(RoutingResult(
                    alert_id=alert.id,
                    provider=providers[i],
                    incident_id=None,
                    escalation_policy=policy_name,
                    success=False,
                    error=str(result)
                ))
            else:
                results.append(result)
        
        return results
    
    async def _create_provider_incident(self, alert: AlertData, provider: str, policy: Dict, policy_name: str) -> RoutingResult:
        """Create incident in specific provider"""
        try:
            if provider == "pagerduty":
                incident_id = await self.incident_manager.create_pagerduty_incident(alert, policy)
            elif provider == "opsgenie":
                incident_id = await self.incident_manager.create_opsgenie_incident(alert, policy)
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            return RoutingResult(
                alert_id=alert.id,
                provider=provider,
                incident_id=incident_id,
                escalation_policy=policy_name,
                success=True
            )
            
        except Exception as e:
            logger.error("Failed to create incident", provider=provider, error=str(e))
            return RoutingResult(
                alert_id=alert.id,
                provider=provider,
                incident_id=None,
                escalation_policy=policy_name,
                success=False,
                error=str(e)
            )
    
    async def _create_local_incident(self, alert: AlertData, policy_name: str) -> str:
        """Create a local incident when external APIs fail"""
        from datetime import datetime, timezone
        import uuid
        
        incident_id = f"local_{uuid.uuid4().hex[:8]}"
        
        # Get policy details
        policy = self.escalation_policies.get(policy_name, {})
        
        # Store in incident manager's active_incidents
        self.incident_manager.active_incidents[incident_id] = {
            "id": incident_id,
            "provider": "local",
            "alert_id": alert.id,
            "title": alert.title,
            "message": alert.description,
            "status": "triggered",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "service": {"summary": alert.service_name},
            "entity": alert.service_name,
            "severity": alert.severity.value,
            "source": alert.source.value,
            "tags": alert.tags,
            "escalation_policy": policy_name
        }
        
        logger.info("Local incident created", incident_id=incident_id, alert_id=alert.id)
        return incident_id
