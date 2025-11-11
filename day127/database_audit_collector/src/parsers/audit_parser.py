import json
from typing import Dict, Any, List
from datetime import datetime
import logging

class AuditLogParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def normalize_audit_log(self, raw_log: Dict[str, Any], db_type: str) -> Dict[str, Any]:
        """Normalize audit log to standard format"""
        try:
            normalized = {
                "timestamp": raw_log.get("timestamp", datetime.now().isoformat()),
                "database_type": db_type,
                "instance": raw_log.get("instance", "unknown"),
                "user": raw_log.get("user", "unknown"),
                "operation": raw_log.get("operation", "unknown"),
                "success": raw_log.get("success", True),
                "source_ip": raw_log.get("source_ip", "unknown"),
                "metadata": {
                    "parser_version": "1.0.0",
                    "processed_at": datetime.now().isoformat()
                }
            }
            
            # Database-specific fields
            if db_type == "postgresql":
                normalized.update({
                    "query": raw_log.get("query", ""),
                    "result_rows": raw_log.get("result_rows", 0),
                    "total_time_ms": raw_log.get("total_time_ms", 0),
                    "execution_count": raw_log.get("execution_count", 1)
                })
            elif db_type == "mysql":
                normalized.update({
                    "query": raw_log.get("query", ""),
                    "result_rows": raw_log.get("result_rows", 0),
                    "duration_seconds": raw_log.get("duration_seconds", 0),
                    "rows_examined": raw_log.get("rows_examined", 0)
                })
            elif db_type == "mongodb":
                normalized.update({
                    "collection": raw_log.get("collection", ""),
                    "query": raw_log.get("query", ""),
                    "result_docs": raw_log.get("result_docs", 0),
                    "duration_ms": raw_log.get("duration_ms", 0)
                })
                
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing audit log: {e}")
            return {}
    
    def parse_batch(self, raw_logs: List[Dict[str, Any]], db_type: str) -> List[Dict[str, Any]]:
        """Parse a batch of raw audit logs"""
        normalized_logs = []
        for raw_log in raw_logs:
            normalized = self.normalize_audit_log(raw_log, db_type)
            if normalized:
                normalized_logs.append(normalized)
        
        self.logger.info(f"Parsed {len(normalized_logs)}/{len(raw_logs)} audit logs for {db_type}")
        return normalized_logs
