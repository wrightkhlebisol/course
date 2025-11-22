"""
Webhook Handler - Process webhooks from PagerDuty and OpsGenie
Handles acknowledgments, status updates, and incident synchronization
"""

import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import HTTPException
from core.config import get_settings

logger = structlog.get_logger()

class WebhookHandler:
    """Handles incoming webhooks from external incident management systems"""
    
    def __init__(self, incident_manager, alert_router):
        self.incident_manager = incident_manager
        self.alert_router = alert_router
        self.settings = get_settings()
        
    async def handle_pagerduty_webhook(self, body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """Process PagerDuty webhook"""
        try:
            # Validate webhook signature if configured
            if self.settings.enable_webhook_validation and self.settings.pagerduty_webhook_secret:
                self._validate_pagerduty_signature(body, headers)
            
            # Parse webhook payload
            payload = json.loads(body)
            messages = payload.get("messages", [])
            
            processed_events = []
            for message in messages:
                event_result = await self._process_pagerduty_event(message)
                processed_events.append(event_result)
            
            logger.info("Processed PagerDuty webhook", events=len(processed_events))
            
            return {
                "status": "success",
                "processed_events": len(processed_events),
                "events": processed_events
            }
            
        except Exception as e:
            logger.error("Failed to process PagerDuty webhook", error=str(e))
            raise HTTPException(status_code=400, detail=str(e))
    
    async def handle_opsgenie_webhook(self, body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """Process OpsGenie webhook"""
        try:
            # Validate webhook signature if configured
            if self.settings.enable_webhook_validation and self.settings.opsgenie_webhook_secret:
                self._validate_opsgenie_signature(body, headers)
            
            # Parse webhook payload
            payload = json.loads(body)
            
            event_result = await self._process_opsgenie_event(payload)
            
            logger.info("Processed OpsGenie webhook", event_type=payload.get("action"))
            
            return {
                "status": "success", 
                "event": event_result
            }
            
        except Exception as e:
            logger.error("Failed to process OpsGenie webhook", error=str(e))
            raise HTTPException(status_code=400, detail=str(e))
    
    def _validate_pagerduty_signature(self, body: bytes, headers: Dict[str, str]):
        """Validate PagerDuty webhook signature"""
        signature = headers.get("x-pagerduty-signature")
        if not signature:
            raise ValueError("Missing PagerDuty signature")
        
        expected = hmac.new(
            self.settings.pagerduty_webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(f"v1={expected}", signature):
            raise ValueError("Invalid PagerDuty signature")
    
    def _validate_opsgenie_signature(self, body: bytes, headers: Dict[str, str]):
        """Validate OpsGenie webhook signature"""
        signature = headers.get("x-opsgenie-signature")
        if not signature:
            raise ValueError("Missing OpsGenie signature")
        
        expected = hashlib.sha256(
            (self.settings.opsgenie_webhook_secret + body.decode()).encode()
        ).hexdigest()
        
        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid OpsGenie signature")
    
    async def _process_pagerduty_event(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual PagerDuty event"""
        event_type = message.get("event")
        incident = message.get("incident", {})
        incident_id = incident.get("id")
        
        if not incident_id:
            return {"status": "skipped", "reason": "no_incident_id"}
        
        # Update local incident tracking
        if incident_id in self.incident_manager.active_incidents:
            self.incident_manager.active_incidents[incident_id]["last_updated"] = datetime.now()
            self.incident_manager.active_incidents[incident_id]["status"] = incident.get("status")
        
        # Process different event types
        if event_type == "incident.acknowledged":
            await self._handle_incident_acknowledged(incident_id, "pagerduty", incident)
        elif event_type == "incident.resolved":
            await self._handle_incident_resolved(incident_id, "pagerduty", incident)
        elif event_type == "incident.escalated":
            await self._handle_incident_escalated(incident_id, "pagerduty", incident)
        
        return {
            "status": "processed",
            "event_type": event_type,
            "incident_id": incident_id
        }
    
    async def _process_opsgenie_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process OpsGenie webhook event"""
        action = payload.get("action")
        alert = payload.get("alert", {})
        alert_id = alert.get("alertId")
        
        if not alert_id:
            return {"status": "skipped", "reason": "no_alert_id"}
        
        # Update local incident tracking
        if alert_id in self.incident_manager.active_incidents:
            self.incident_manager.active_incidents[alert_id]["last_updated"] = datetime.now()
            self.incident_manager.active_incidents[alert_id]["status"] = alert.get("status")
        
        # Process different actions
        if action == "Acknowledged":
            await self._handle_incident_acknowledged(alert_id, "opsgenie", alert)
        elif action == "Closed":
            await self._handle_incident_resolved(alert_id, "opsgenie", alert)
        elif action == "Escalated":
            await self._handle_incident_escalated(alert_id, "opsgenie", alert)
        
        return {
            "status": "processed",
            "action": action,
            "alert_id": alert_id
        }
    
    async def _handle_incident_acknowledged(self, incident_id: str, provider: str, incident_data: Dict):
        """Handle incident acknowledgment"""
        logger.info("Incident acknowledged", 
                   incident_id=incident_id, 
                   provider=provider)
        
        # Update incident status and stop escalation
        if incident_id in self.incident_manager.active_incidents:
            self.incident_manager.active_incidents[incident_id]["acknowledged"] = True
            self.incident_manager.active_incidents[incident_id]["acknowledged_by"] = incident_data.get("acknowledged_by")
    
    async def _handle_incident_resolved(self, incident_id: str, provider: str, incident_data: Dict):
        """Handle incident resolution"""
        logger.info("Incident resolved", 
                   incident_id=incident_id,
                   provider=provider)
        
        # Mark incident as resolved and trigger post-incident workflows
        if incident_id in self.incident_manager.active_incidents:
            self.incident_manager.active_incidents[incident_id]["resolved"] = True
            self.incident_manager.active_incidents[incident_id]["resolved_by"] = incident_data.get("resolved_by")
    
    async def _handle_incident_escalated(self, incident_id: str, provider: str, incident_data: Dict):
        """Handle incident escalation"""
        logger.info("Incident escalated",
                   incident_id=incident_id,
                   provider=provider)
        
        # Update escalation tracking
        if incident_id in self.incident_manager.active_incidents:
            escalations = self.incident_manager.active_incidents[incident_id].get("escalations", 0)
            self.incident_manager.active_incidents[incident_id]["escalations"] = escalations + 1
