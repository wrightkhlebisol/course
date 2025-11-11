import mysql.connector
import json
from typing import List, Dict, Any
from datetime import datetime
import logging

class MySQLAuditCollector:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self.last_timestamp = None
        self._connection_warned = False
        
    def collect_audit_logs(self) -> List[Dict[str, Any]]:
        """Collect audit logs from MySQL"""
        try:
            pool = self.connection_manager.get_connection('mysql')
            if not pool:
                if not self._connection_warned:
                    self.logger.warning("MySQL connection pool not available - skipping collection")
                    self._connection_warned = True
                return []
                
            conn = pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Simulate MySQL audit log collection from performance_schema
            query = """
            SELECT 
                NOW() as timestamp,
                'mysql' as database_type,
                @@hostname as instance,
                USER() as user,
                SUBSTRING(SQL_TEXT, 1, 100) as operation,
                TIMER_WAIT/1000000000 as duration_seconds,
                ROWS_EXAMINED,
                ROWS_SENT
            FROM performance_schema.events_statements_history_long
            WHERE TIMER_START > COALESCE(%s, 0)
            ORDER BY TIMER_START DESC
            LIMIT 1000
            """
            
            cursor.execute(query, (self.last_timestamp,))
            rows = cursor.fetchall()
            
            audit_logs = []
            for row in rows:
                audit_log = {
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else datetime.now().isoformat(),
                    "database_type": row['database_type'],
                    "instance": row['instance'],
                    "user": row['user'],
                    "operation": self._extract_operation_type(row['operation'] or ''),
                    "query": row['operation'] or 'N/A',
                    "duration_seconds": float(row['duration_seconds'] or 0),
                    "rows_examined": row['ROWS_EXAMINED'] or 0,
                    "result_rows": row['ROWS_SENT'] or 0,
                    "success": True,
                    "source_ip": "127.0.0.1"
                }
                audit_logs.append(audit_log)
            
            cursor.close()
            conn.close()
            
            if audit_logs:
                self.last_timestamp = datetime.now()
                
            self.logger.info(f"Collected {len(audit_logs)} MySQL audit logs")
            return audit_logs
            
        except Exception as e:
            self.logger.error(f"Error collecting MySQL audit logs: {e}")
            return []
    
    def _extract_operation_type(self, query: str) -> str:
        """Extract operation type from SQL query"""
        if not query:
            return 'OTHER'
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
