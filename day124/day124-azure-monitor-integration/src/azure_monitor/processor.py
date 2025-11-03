import asyncio
import json
from datetime import datetime
from typing import Dict, List, AsyncGenerator
from collections import defaultdict

import structlog
from azure_monitor.connector import AzureLogEntry

logger = structlog.get_logger()

class AzureLogProcessor:
    """Process Azure Monitor logs and extract insights"""
    
    def __init__(self):
        self.stats = defaultdict(int)
        self.log_buffer = []
        self.error_patterns = []
        self.performance_metrics = defaultdict(list)
        
    async def process_log_entry(self, entry: AzureLogEntry) -> Dict:
        """Process individual Azure log entry"""
        self.stats['total_processed'] += 1
        self.stats[f'table_{entry.table_name}'] += 1
        self.stats[f'level_{entry.level}'] += 1
        
        # Extract insights based on log type
        insights = {}
        
        if entry.table_name == 'AppTraces':
            insights.update(self._process_application_log(entry))
        elif entry.table_name == 'SecurityEvent':
            insights.update(self._process_security_log(entry))
        elif entry.table_name == 'Perf':
            insights.update(self._process_performance_log(entry))
        
        # Add to buffer for real-time display
        processed_entry = {
            'id': f"{entry.workspace_id}_{self.stats['total_processed']}",
            'timestamp': entry.timestamp,
            'workspace': entry.workspace_id,
            'table': entry.table_name,
            'level': entry.level,
            'message': entry.message,
            'resource': entry.resource_name or 'unknown',
            'subscription': entry.subscription_id,
            'insights': insights,
            'source': 'azure_monitor'
        }
        
        self.log_buffer.append(processed_entry)
        if len(self.log_buffer) > 100:
            self.log_buffer.pop(0)  # Keep only recent entries
            
        return processed_entry
    
    def _process_application_log(self, entry: AzureLogEntry) -> Dict:
        """Process application-specific logs"""
        insights = {}
        
        message = entry.message.lower()
        
        if 'error' in message or 'exception' in message:
            insights['type'] = 'application_error'
            insights['severity'] = 'high'
            self.stats['application_errors'] += 1
        elif 'warning' in message:
            insights['type'] = 'application_warning' 
            insights['severity'] = 'medium'
        elif 'started' in message or 'initialized' in message:
            insights['type'] = 'application_lifecycle'
            insights['severity'] = 'low'
        
        return insights
    
    def _process_security_log(self, entry: AzureLogEntry) -> Dict:
        """Process security-specific logs"""
        insights = {}
        
        message = entry.message.lower()
        
        if 'failed' in message or 'denied' in message:
            insights['type'] = 'security_incident'
            insights['severity'] = 'critical'
            self.stats['security_incidents'] += 1
        elif 'authentication' in message or 'login' in message:
            insights['type'] = 'authentication_event'
            insights['severity'] = 'medium'
        
        return insights
    
    def _process_performance_log(self, entry: AzureLogEntry) -> Dict:
        """Process performance-specific logs"""
        insights = {}
        
        try:
            # Extract performance counter value if available
            raw_data = entry.raw_data
            if 'CounterValue' in raw_data:
                value = float(raw_data['CounterValue'])
                self.performance_metrics['cpu_usage'].append(value)
                
                if value > 80:
                    insights['type'] = 'performance_alert'
                    insights['severity'] = 'high'
                    insights['metric'] = 'cpu_high'
                    self.stats['performance_alerts'] += 1
                    
        except (ValueError, KeyError):
            pass
            
        return insights
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent processed logs"""
        return self.log_buffer[-limit:] if self.log_buffer else []
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        stats = dict(self.stats)
        
        # Add performance metrics summary
        if self.performance_metrics['cpu_usage']:
            cpu_values = self.performance_metrics['cpu_usage'][-10:]  # Last 10 values
            stats['avg_cpu_usage'] = sum(cpu_values) / len(cpu_values)
            stats['max_cpu_usage'] = max(cpu_values)
        
        return stats
    
    def get_insights_summary(self) -> Dict:
        """Get high-level insights summary"""
        return {
            'total_logs_processed': self.stats['total_processed'],
            'application_errors': self.stats.get('application_errors', 0),
            'security_incidents': self.stats.get('security_incidents', 0),
            'performance_alerts': self.stats.get('performance_alerts', 0),
            'workspaces_active': len(set(entry.get('workspace', '') for entry in self.log_buffer)),
            'last_processed': datetime.now().isoformat()
        }
