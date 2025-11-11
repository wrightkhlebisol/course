import asyncio
import asyncpg
import json
from typing import List, Dict, Any
from datetime import datetime
import logging

class PostgreSQLAuditCollector:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self.last_timestamp = None
        self._connection_warned = False
        
    async def collect_audit_logs(self) -> List[Dict[str, Any]]:
        """Collect audit logs from PostgreSQL"""
        try:
            pool = self.connection_manager.get_connection('postgresql')
            if not pool:
                if not self._connection_warned:
                    self.logger.warning("PostgreSQL connection pool not available - skipping collection")
                    self._connection_warned = True
                return []
                
            async with pool.acquire() as conn:
                # Query pg_stat_statements for query activity
                query = """
                SELECT 
                    now() as timestamp,
                    'postgresql' as database_type,
                    current_database() as instance,
                    current_user as user,
                    substring(query, 1, 100) as operation,
                    calls as execution_count,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE last_call > COALESCE($1, '1970-01-01'::timestamp)
                ORDER BY last_call DESC
                LIMIT 1000
                """
                
                rows = await conn.fetch(query, self.last_timestamp)
                
                audit_logs = []
                for row in rows:
                    audit_log = {
                        "timestamp": row['timestamp'].isoformat(),
                        "database_type": row['database_type'],
                        "instance": row['instance'],
                        "user": row['user'],
                        "operation": self._extract_operation_type(row['operation']),
                        "query": row['operation'],
                        "execution_count": row['execution_count'],
                        "total_time_ms": float(row['total_time']),
                        "mean_time_ms": float(row['mean_time']),
                        "result_rows": row['rows'],
                        "success": True,
                        "source_ip": "127.0.0.1"  # Would be extracted from actual audit logs
                    }
                    audit_logs.append(audit_log)
                
                if audit_logs:
                    self.last_timestamp = datetime.now()
                    
                self.logger.info(f"Collected {len(audit_logs)} PostgreSQL audit logs")
                return audit_logs
                
        except Exception as e:
            self.logger.error(f"Error collecting PostgreSQL audit logs: {e}")
            return []
    
    def _extract_operation_type(self, query: str) -> str:
        """Extract operation type from SQL query"""
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'
