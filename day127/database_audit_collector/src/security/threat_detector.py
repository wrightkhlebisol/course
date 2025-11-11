import json
from typing import Dict, Any, List
from datetime import datetime, time
import logging
import yaml

class SecurityThreatDetector:
    def __init__(self, config_path: str = "config/database_config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['security']['threat_detection']
        self.logger = logging.getLogger(__name__)
        self.user_activity = {}
        
    def analyze_audit_log(self, audit_log: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze audit log for security threats"""
        threats = []
        
        # Check for privilege escalation
        if self._is_privilege_escalation(audit_log):
            threats.append({
                "type": "privilege_escalation",
                "severity": "high",
                "description": f"User {audit_log['user']} performed privileged operation {audit_log['operation']}",
                "audit_log": audit_log,
                "timestamp": datetime.now().isoformat()
            })
        
        # Check for off-hours access
        if self._is_off_hours_access(audit_log):
            threats.append({
                "type": "off_hours_access",
                "severity": "medium",
                "description": f"Off-hours database access by {audit_log['user']}",
                "audit_log": audit_log,
                "timestamp": datetime.now().isoformat()
            })
        
        # Check for bulk data access
        if self._is_bulk_data_access(audit_log):
            threats.append({
                "type": "bulk_data_access",
                "severity": "high",
                "description": f"Large data access detected: {audit_log.get('result_rows', 0)} rows",
                "audit_log": audit_log,
                "timestamp": datetime.now().isoformat()
            })
        
        # Track user activity for failed login detection
        self._track_user_activity(audit_log)
        
        # Check for failed login spikes
        failed_login_threat = self._check_failed_logins(audit_log)
        if failed_login_threat:
            threats.append(failed_login_threat)
        
        if threats:
            self.logger.warning(f"Detected {len(threats)} security threats in audit log")
        
        return threats
    
    def _is_privilege_escalation(self, audit_log: Dict[str, Any]) -> bool:
        """Check if audit log indicates privilege escalation"""
        privileged_operations = ['CREATE USER', 'GRANT', 'ALTER USER', 'DROP USER']
        operation = audit_log.get('operation', '').upper()
        return any(priv_op in operation for priv_op in privileged_operations)
    
    def _is_off_hours_access(self, audit_log: Dict[str, Any]) -> bool:
        """Check if access is during off hours"""
        try:
            timestamp = datetime.fromisoformat(audit_log['timestamp'].replace('Z', '+00:00'))
            current_time = timestamp.time()
            
            off_hours_start = time.fromisoformat(self.config['off_hours_start'])
            off_hours_end = time.fromisoformat(self.config['off_hours_end'])
            
            if off_hours_start > off_hours_end:  # Overnight period
                return current_time >= off_hours_start or current_time <= off_hours_end
            else:
                return off_hours_start <= current_time <= off_hours_end
        except:
            return False
    
    def _is_bulk_data_access(self, audit_log: Dict[str, Any]) -> bool:
        """Check if access involves bulk data"""
        result_rows = audit_log.get('result_rows', 0)
        result_docs = audit_log.get('result_docs', 0)
        threshold = self.config['bulk_data_threshold']
        
        return result_rows > threshold or result_docs > threshold
    
    def _track_user_activity(self, audit_log: Dict[str, Any]):
        """Track user activity for pattern analysis"""
        user = audit_log.get('user', 'unknown')
        if user not in self.user_activity:
            self.user_activity[user] = {'failed_logins': 0, 'last_activity': None}
        
        self.user_activity[user]['last_activity'] = audit_log.get('timestamp')
        
        if not audit_log.get('success', True):
            self.user_activity[user]['failed_logins'] += 1
    
    def _check_failed_logins(self, audit_log: Dict[str, Any]) -> Dict[str, Any]:
        """Check for failed login spikes"""
        user = audit_log.get('user', 'unknown')
        if user in self.user_activity:
            failed_count = self.user_activity[user]['failed_logins']
            if failed_count >= self.config['failed_login_threshold']:
                # Reset counter after detection
                self.user_activity[user]['failed_logins'] = 0
                return {
                    "type": "failed_login_spike",
                    "severity": "high",
                    "description": f"Multiple failed login attempts by {user}: {failed_count} attempts",
                    "audit_log": audit_log,
                    "timestamp": datetime.now().isoformat()
                }
        return None
