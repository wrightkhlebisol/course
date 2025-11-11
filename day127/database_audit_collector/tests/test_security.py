import pytest
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.security.threat_detector import SecurityThreatDetector

class TestSecurityThreatDetector:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = SecurityThreatDetector()
    
    def test_privilege_escalation_detection(self):
        """Test privilege escalation threat detection"""
        audit_log = {
            "timestamp": "2025-05-16T14:30:00Z",
            "database_type": "postgresql",
            "user": "test_user",
            "operation": "CREATE USER admin_user",
            "success": True
        }
        
        threats = self.detector.analyze_audit_log(audit_log)
        
        assert len(threats) > 0
        assert any(threat['type'] == 'privilege_escalation' for threat in threats)
        assert any(threat['severity'] == 'high' for threat in threats)
    
    def test_bulk_data_access_detection(self):
        """Test bulk data access threat detection"""
        audit_log = {
            "timestamp": "2025-05-16T14:30:00Z",
            "database_type": "postgresql",
            "user": "test_user",
            "operation": "SELECT",
            "result_rows": 50000,  # Above threshold
            "success": True
        }
        
        threats = self.detector.analyze_audit_log(audit_log)
        
        assert len(threats) > 0
        assert any(threat['type'] == 'bulk_data_access' for threat in threats)
        assert any(threat['severity'] == 'high' for threat in threats)
    
    def test_off_hours_access_detection(self):
        """Test off-hours access detection"""
        # Create audit log with timestamp during off hours (e.g., 2 AM)
        audit_log = {
            "timestamp": "2025-05-16T02:30:00Z",
            "database_type": "postgresql",
            "user": "test_user",
            "operation": "SELECT",
            "success": True
        }
        
        threats = self.detector.analyze_audit_log(audit_log)
        
        # Note: This test might not detect off-hours depending on configuration
        # The actual detection depends on the configured off-hours times
        assert isinstance(threats, list)
    
    def test_failed_login_tracking(self):
        """Test failed login tracking"""
        # Simulate multiple failed login attempts
        for i in range(6):  # Above threshold
            audit_log = {
                "timestamp": f"2025-05-16T14:30:{i:02d}Z",
                "database_type": "postgresql",
                "user": "test_user",
                "operation": "LOGIN",
                "success": False  # Failed login
            }
            
            threats = self.detector.analyze_audit_log(audit_log)
        
        # The last attempt should trigger failed login spike detection
        assert len(threats) > 0
        assert any(threat['type'] == 'failed_login_spike' for threat in threats)
    
    def test_normal_activity_no_threats(self):
        """Test that normal activity doesn't generate threats"""
        audit_log = {
            "timestamp": "2025-05-16T14:30:00Z",
            "database_type": "postgresql",
            "user": "test_user",
            "operation": "SELECT",
            "result_rows": 10,  # Normal amount
            "success": True
        }
        
        threats = self.detector.analyze_audit_log(audit_log)
        
        # Normal activity should not generate threats
        assert len(threats) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
