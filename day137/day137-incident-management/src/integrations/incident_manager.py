"""
Incident Manager - Integration with PagerDuty and OpsGenie APIs
Handles incident creation, updates, and synchronization
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import httpx
import structlog
from core.config import get_settings

logger = structlog.get_logger()

class IncidentManager:
    """Manages incidents across multiple external systems"""
    
    def __init__(self, pagerduty_api_key: str, opsgenie_api_key: str):
        self.settings = get_settings()
        self.pagerduty_api_key = pagerduty_api_key
        self.opsgenie_api_key = opsgenie_api_key
        self.active_incidents = {}
        
        # HTTP clients with proper configuration
        self.pagerduty_client = None
        self.opsgenie_client = None
    
    async def initialize(self):
        """Initialize HTTP clients and validate connectivity"""
        timeout = httpx.Timeout(10.0, connect=5.0)
        
        self.pagerduty_client = httpx.AsyncClient(
            base_url="https://api.pagerduty.com",
            headers={
                "Authorization": f"Token token={self.pagerduty_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.pagerduty+json;version=2"
            },
            timeout=timeout
        )
        
        self.opsgenie_client = httpx.AsyncClient(
            base_url="https://api.opsgenie.com/v2",
            headers={
                "Authorization": f"GenieKey {self.opsgenie_api_key}",
                "Content-Type": "application/json"
            },
            timeout=timeout
        )
        
        # Test connectivity
        await self._test_connectivity()
        logger.info("Incident manager initialized successfully")
    
    async def cleanup(self):
        """Cleanup HTTP clients"""
        if self.pagerduty_client:
            await self.pagerduty_client.aclose()
        if self.opsgenie_client:
            await self.opsgenie_client.aclose()
    
    async def _test_connectivity(self):
        """Test connectivity to external APIs"""
        try:
            # Test PagerDuty
            if self.settings.enable_pagerduty:
                response = await self.pagerduty_client.get("/users", params={"limit": 1})
                if response.status_code == 200:
                    logger.info("PagerDuty connectivity verified")
                else:
                    logger.warning("PagerDuty connectivity issues", status=response.status_code)
            
            # Test OpsGenie  
            if self.settings.enable_opsgenie:
                response = await self.opsgenie_client.get("/account")
                if response.status_code == 200:
                    logger.info("OpsGenie connectivity verified")
                else:
                    logger.warning("OpsGenie connectivity issues", status=response.status_code)
                    
        except Exception as e:
            logger.error("Connectivity test failed", error=str(e))
    
    async def create_pagerduty_incident(self, alert_data, policy: Dict) -> str:
        """Create incident in PagerDuty"""
        if not self.settings.enable_pagerduty:
            raise Exception("PagerDuty integration disabled")
        
        # Map internal severity to PagerDuty severity
        severity_mapping = {
            "critical": "critical",
            "high": "error", 
            "medium": "warning",
            "low": "info",
            "info": "info"
        }
        
        incident_payload = {
            "incident": {
                "type": "incident",
                "title": alert_data.title,
                "service": {
                    "id": "PSERVICE",  # Default service ID for demo
                    "type": "service_reference"
                },
                "priority": {
                    "id": "P1" if alert_data.severity.value == "critical" else "P2",
                    "type": "priority_reference"
                },
                "urgency": "high" if alert_data.severity.value in ["critical", "high"] else "low",
                "body": {
                    "type": "incident_body",
                    "details": json.dumps({
                        "description": alert_data.description,
                        "source": alert_data.source.value,
                        "service_name": alert_data.service_name,
                        "metadata": alert_data.metadata,
                        "tags": alert_data.tags
                    }, indent=2)
                }
            }
        }
        
        try:
            response = await self.pagerduty_client.post("/incidents", json=incident_payload)
            response.raise_for_status()
            
            result = response.json()
            incident_id = result["incident"]["id"]
            
            # Store incident locally
            self.active_incidents[incident_id] = {
                "provider": "pagerduty",
                "alert_id": alert_data.id,
                "created_at": datetime.now(timezone.utc),
                "status": "triggered"
            }
            
            logger.info("PagerDuty incident created", 
                       incident_id=incident_id, 
                       alert_id=alert_data.id)
            
            return incident_id
            
        except httpx.HTTPStatusError as e:
            logger.error("PagerDuty API error", 
                        status=e.response.status_code,
                        response=e.response.text)
            raise Exception(f"PagerDuty API error: {e.response.status_code}")
        except Exception as e:
            logger.error("PagerDuty incident creation failed", error=str(e))
            raise
    
    async def create_opsgenie_incident(self, alert_data, policy: Dict) -> str:
        """Create alert in OpsGenie"""
        if not self.settings.enable_opsgenie:
            raise Exception("OpsGenie integration disabled")
        
        # Map internal severity to OpsGenie priority
        priority_mapping = {
            "critical": "P1",
            "high": "P2",
            "medium": "P3", 
            "low": "P4",
            "info": "P5"
        }
        
        alert_payload = {
            "message": alert_data.title,
            "description": alert_data.description,
            "priority": priority_mapping.get(alert_data.severity.value, "P3"),
            "source": alert_data.source.value,
            "entity": alert_data.service_name,
            "alias": f"alert_{alert_data.id}",
            "details": {
                "service_name": alert_data.service_name,
                "team": alert_data.team,
                "metadata": json.dumps(alert_data.metadata),
                "tags": ",".join(alert_data.tags)
            },
            "tags": alert_data.tags
        }
        
        try:
            response = await self.opsgenie_client.post("/alerts", json=alert_payload)
            response.raise_for_status()
            
            result = response.json()
            alert_id = result["requestId"]
            
            # Store incident locally
            self.active_incidents[alert_id] = {
                "provider": "opsgenie",
                "alert_id": alert_data.id,
                "created_at": datetime.now(timezone.utc),
                "status": "open"
            }
            
            logger.info("OpsGenie alert created",
                       incident_id=alert_id,
                       alert_id=alert_data.id)
            
            return alert_id
            
        except httpx.HTTPStatusError as e:
            logger.error("OpsGenie API error",
                        status=e.response.status_code, 
                        response=e.response.text)
            raise Exception(f"OpsGenie API error: {e.response.status_code}")
        except Exception as e:
            logger.error("OpsGenie alert creation failed", error=str(e))
            raise
    
    async def get_all_incidents(self) -> Dict[str, List[Dict]]:
        """Get incidents from all providers"""
        pagerduty_incidents = []
        opsgenie_incidents = []
        
        try:
            if self.settings.enable_pagerduty and self.pagerduty_client:
                pd_response = await self.pagerduty_client.get("/incidents", params={"limit": 50})
                if pd_response.status_code == 200:
                    pagerduty_incidents = pd_response.json().get("incidents", [])
        except Exception as e:
            logger.error("Failed to fetch PagerDuty incidents", error=str(e))
        
        try:
            if self.settings.enable_opsgenie and self.opsgenie_client:
                og_response = await self.opsgenie_client.get("/alerts", params={"limit": 50})
                if og_response.status_code == 200:
                    opsgenie_incidents = og_response.json().get("data", [])
        except Exception as e:
            logger.error("Failed to fetch OpsGenie alerts", error=str(e))
        
        # Format local incidents for frontend
        local_incidents = []
        for incident_id, incident_data in self.active_incidents.items():
            local_incidents.append({
                "id": incident_id,
                "incident_id": incident_id,
                "title": incident_data.get("title", incident_data.get("message", "Unknown")),
                "message": incident_data.get("message", incident_data.get("title", "Unknown")),
                "status": incident_data.get("status", "triggered"),
                "created_at": incident_data.get("created_at", incident_data.get("createdAt", "")),
                "createdAt": incident_data.get("createdAt", incident_data.get("created_at", "")),
                "service": incident_data.get("service", {}),
                "entity": incident_data.get("entity", incident_data.get("service_name", "")),
                "severity": incident_data.get("severity", "medium"),
                "source": incident_data.get("source", "application"),
                "tags": incident_data.get("tags", [])
            })
        
        return {
            "pagerduty": pagerduty_incidents,
            "opsgenie": opsgenie_incidents,
            "local_incidents": local_incidents
        }
