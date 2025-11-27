import random
import uuid
from datetime import datetime
from typing import List
from ..models.alert import LogAlert, AlertSeverity

class AlertGenerator:
    """Generate sample alerts for testing"""
    
    SERVICES = ["payment", "database", "api", "frontend", "security"]
    COMPONENTS = ["processor", "gateway", "cache", "auth", "validator"]
    
    ALERT_TEMPLATES = {
        AlertSeverity.CRITICAL: [
            "Service completely unavailable",
            "Database connection pool exhausted", 
            "Payment processing failed for all transactions",
            "Security breach detected"
        ],
        AlertSeverity.ERROR: [
            "High error rate detected",
            "Memory usage above 90%",
            "Failed to process user requests",
            "Database timeout errors"
        ],
        AlertSeverity.WARNING: [
            "Response time degradation",
            "Disk space running low",
            "Unusual traffic pattern detected",
            "Cache miss rate elevated"
        ],
        AlertSeverity.INFO: [
            "Deployment completed successfully",
            "Scheduled maintenance starting",
            "Configuration updated",
            "Health check passed"
        ]
    }
    
    def generate_alert(self, severity: AlertSeverity = None) -> LogAlert:
        """Generate a random alert"""
        if not severity:
            severity = random.choice(list(AlertSeverity))
        
        service = random.choice(self.SERVICES)
        component = random.choice(self.COMPONENTS)
        title = random.choice(self.ALERT_TEMPLATES[severity])
        
        alert = LogAlert(
            id=str(uuid.uuid4()),
            title=title,
            message=f"Alert detected in {service} {component}: {title}",
            severity=severity,
            service=service,
            component=component,
            timestamp=datetime.now(),
            metadata={
                "correlation_id": str(uuid.uuid4()),
                "source": "log_processor",
                "environment": "production"
            },
            affected_users=random.randint(1, 1000) if severity in [AlertSeverity.CRITICAL, AlertSeverity.ERROR] else None,
            dashboard_url=f"https://dashboard.example.com/{service}",
            runbook_url=f"https://runbook.example.com/{service}_{component}",
            raw_logs=[
                f"ERROR: {title} at {datetime.now().isoformat()}",
                f"Stack trace: sample error in {component}",
                f"Request ID: {uuid.uuid4()}"
            ]
        )
        
        return alert
    
    def generate_batch(self, count: int) -> List[LogAlert]:
        """Generate multiple alerts"""
        return [self.generate_alert() for _ in range(count)]
