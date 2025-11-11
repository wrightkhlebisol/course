import pytest
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parsers.audit_parser import AuditLogParser

class TestAuditParser:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = AuditLogParser()
        
    def test_normalize_postgresql_log(self):
        """Test PostgreSQL log normalization"""
        raw_log = {
            "timestamp": "2025-05-16T14:30:00Z",
            "instance": "localhost:5432",
            "user": "test_user",
            "operation": "SELECT",
            "query": "SELECT * FROM users",
            "result_rows": 100,
            "total_time_ms": 50,
            "execution_count": 1,
            "success": True,
            "source_ip": "127.0.0.1"
        }
        
        normalized = self.parser.normalize_audit_log(raw_log, "postgresql")
        
        assert normalized["database_type"] == "postgresql"
        assert normalized["operation"] == "SELECT"
        assert normalized["query"] == "SELECT * FROM users"
        assert normalized["result_rows"] == 100
        assert "metadata" in normalized
        assert "parser_version" in normalized["metadata"]
    
    def test_normalize_mysql_log(self):
        """Test MySQL log normalization"""
        raw_log = {
            "timestamp": "2025-05-16T14:30:00Z",
            "instance": "localhost:3306",
            "user": "test_user",
            "operation": "INSERT",
            "query": "INSERT INTO orders VALUES (...)",
            "result_rows": 1,
            "duration_seconds": 0.05,
            "rows_examined": 0,
            "success": True,
            "source_ip": "127.0.0.1"
        }
        
        normalized = self.parser.normalize_audit_log(raw_log, "mysql")
        
        assert normalized["database_type"] == "mysql"
        assert normalized["operation"] == "INSERT"
        assert normalized["duration_seconds"] == 0.05
        assert normalized["rows_examined"] == 0
        
    def test_normalize_mongodb_log(self):
        """Test MongoDB log normalization"""
        raw_log = {
            "timestamp": "2025-05-16T14:30:00Z",
            "instance": "localhost:27017",
            "user": "test_user",
            "operation": "find",
            "collection": "users",
            "query": "db.users.find({})",
            "result_docs": 50,
            "duration_ms": 25,
            "success": True,
            "source_ip": "127.0.0.1"
        }
        
        normalized = self.parser.normalize_audit_log(raw_log, "mongodb")
        
        assert normalized["database_type"] == "mongodb"
        assert normalized["operation"] == "find"
        assert normalized["collection"] == "users"
        assert normalized["result_docs"] == 50
        assert normalized["duration_ms"] == 25
    
    def test_parse_batch(self):
        """Test batch parsing functionality"""
        raw_logs = [
            {
                "timestamp": "2025-05-16T14:30:00Z",
                "instance": "localhost:5432",
                "user": "user1",
                "operation": "SELECT",
                "success": True
            },
            {
                "timestamp": "2025-05-16T14:31:00Z",
                "instance": "localhost:5432",
                "user": "user2",
                "operation": "INSERT",
                "success": True
            }
        ]
        
        normalized_logs = self.parser.parse_batch(raw_logs, "postgresql")
        
        assert len(normalized_logs) == 2
        assert all(log["database_type"] == "postgresql" for log in normalized_logs)
        assert normalized_logs[0]["user"] == "user1"
        assert normalized_logs[1]["user"] == "user2"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
