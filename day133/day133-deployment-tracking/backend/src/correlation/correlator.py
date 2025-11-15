import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import structlog

logger = structlog.get_logger()

class VersionCorrelator:
    def __init__(self, deployment_detector):
        self.deployment_detector = deployment_detector
        self.correlation_cache = {}
        
    async def enrich_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich log entry with deployment context"""
        try:
            # Extract metadata from log entry
            timestamp = self._parse_timestamp(log_entry.get('timestamp'))
            service = log_entry.get('service', 'unknown')
            environment = log_entry.get('environment', 'production')
            
            # Get deployment info for this log
            deployment = self.deployment_detector.get_deployment_for_timestamp(
                timestamp, service, environment
            )
            
            # Add deployment context to log entry
            enriched_entry = log_entry.copy()
            enriched_entry['deployment'] = {
                'version': deployment.version if deployment else 'unknown',
                'deployment_id': deployment.id if deployment else None,
                'commit_hash': deployment.commit_hash if deployment else None,
                'deployment_timestamp': deployment.timestamp.isoformat() if deployment else None
            }
            
            return enriched_entry
            
        except Exception as e:
            logger.error(f"Error enriching log entry: {e}")
            log_entry['deployment'] = {'version': 'unknown', 'error': str(e)}
            return log_entry
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object"""
        try:
            if isinstance(timestamp_str, str):
                # Handle different timestamp formats
                for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
            
            return datetime.now(timezone.utc)
        except:
            return datetime.now(timezone.utc)
    
    async def batch_enrich_logs(self, log_entries: list) -> list:
        """Enrich multiple log entries in batch"""
        enriched_logs = []
        
        for log_entry in log_entries:
            enriched = await self.enrich_log_entry(log_entry)
            enriched_logs.append(enriched)
        
        return enriched_logs
    
    def get_correlation_stats(self) -> Dict:
        """Get correlation statistics"""
        return {
            'cache_size': len(self.correlation_cache),
            'active_deployments': len(self.deployment_detector.active_deployments),
            'total_deployments': len(self.deployment_detector.deployment_history)
        }
