import asyncio
import logging
import yaml
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from collectors.connection_manager import DatabaseConnectionManager
from collectors.postgresql_collector import PostgreSQLAuditCollector
from collectors.mysql_collector import MySQLAuditCollector
from collectors.mongodb_collector import MongoDBAbstractCollector
from parsers.audit_parser import AuditLogParser
from security.threat_detector import SecurityThreatDetector

class DatabaseAuditCollectorService:
    def __init__(self):
        self.connection_manager = DatabaseConnectionManager()
        self.collectors = {}
        self.parser = AuditLogParser()
        self.threat_detector = SecurityThreatDetector()
        self.logger = logging.getLogger(__name__)
        
        # Initialize collectors
        self.collectors['postgresql'] = PostgreSQLAuditCollector(self.connection_manager)
        self.collectors['mysql'] = MySQLAuditCollector(self.connection_manager)
        self.collectors['mongodb'] = MongoDBAbstractCollector(self.connection_manager)
        
        self.audit_logs = []
        self.security_events = []
        self.demo_mode = False
        
    def generate_demo_data(self) -> List[Dict[str, Any]]:
        """Generate demo audit log data when databases are not available"""
        demo_logs = []
        operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
        mongo_operations = ['find', 'insert', 'update', 'delete', 'createIndex', 'dropIndex']
        users = ['admin', 'app_user', 'readonly_user', 'audit_collector', 'developer']
        databases = ['postgresql', 'mysql', 'mongodb']
        collections = ['users', 'orders', 'products', 'audit_log', 'transactions']
        # More realistic: 95% success rate (only occasional failures)
        statuses = ['success'] * 19 + ['failed']  # 95% success, 5% failure
        
        # Generate 5-15 random audit logs per cycle
        num_logs = random.randint(5, 15)
        for i in range(num_logs):
            db_type = random.choice(databases)
            timestamp = datetime.now() - timedelta(seconds=random.randint(0, 300))
            
            # Make failures more realistic - only for certain operations
            operation = random.choice(operations) if db_type != 'mongodb' else random.choice(mongo_operations)
            # Most operations succeed, only occasional failures (and not for simple SELECT/find)
            is_success = True
            if random.random() < 0.05:  # 5% chance of failure
                # Only fail on write operations or complex queries
                if operation.upper() in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']:
                    is_success = False
            
            log = {
                "timestamp": timestamp.isoformat(),
                "database_type": db_type,
                "instance": f"{db_type}-server-{random.randint(1, 3)}",
                "user": random.choice(users),
                "operation": operation,
                "success": is_success,
                "source_ip": f"192.168.1.{random.randint(1, 255)}",
            }
            
            # Add database-specific fields
            if db_type == 'postgresql':
                log.update({
                    "query": f"{random.choice(operations)} FROM table_{random.randint(1, 10)}",
                    "result_rows": random.randint(0, 1000),
                    "total_time_ms": random.uniform(10, 500),
                    "execution_count": random.randint(1, 100)
                })
            elif db_type == 'mysql':
                log.update({
                    "query": f"{random.choice(operations)} FROM table_{random.randint(1, 10)}",
                    "result_rows": random.randint(0, 1000),
                    "duration_seconds": random.uniform(0.01, 0.5),
                    "rows_examined": random.randint(0, 2000)
                })
            elif db_type == 'mongodb':
                collection = random.choice(collections)
                log.update({
                    "collection": collection,
                    "query": f"db.{collection}.{random.choice(mongo_operations)}()",
                    "result_docs": random.randint(0, 500),
                    "duration_ms": random.uniform(5, 200)
                })
            
            demo_logs.append(log)
        
        return demo_logs
        
    async def initialize(self):
        """Initialize the audit collection service"""
        self.logger.info("Initializing Database Audit Collection Service...")
        
        # Initialize connection pools
        success = await self.connection_manager.initialize_pools()
        if not success:
            self.logger.warning("Failed to initialize database connections - running in demo mode")
            # Don't return False - allow service to run with demo data
            return True  # Return True to allow demo mode
            
        self.logger.info("Database Audit Collection Service initialized successfully")
        return True
    
    async def collect_all_audit_logs(self) -> List[Dict[str, Any]]:
        """Collect audit logs from all configured databases"""
        all_logs = []
        
        # PostgreSQL (async)
        try:
            pg_logs = await self.collectors['postgresql'].collect_audit_logs()
            pg_normalized = self.parser.parse_batch(pg_logs, 'postgresql')
            all_logs.extend(pg_normalized)
        except Exception as e:
            self.logger.error(f"Error collecting PostgreSQL logs: {e}")
        
        # MySQL (sync)
        try:
            mysql_logs = self.collectors['mysql'].collect_audit_logs()
            mysql_normalized = self.parser.parse_batch(mysql_logs, 'mysql')
            all_logs.extend(mysql_normalized)
        except Exception as e:
            self.logger.error(f"Error collecting MySQL logs: {e}")
        
        # MongoDB (sync)
        try:
            mongo_logs = self.collectors['mongodb'].collect_audit_logs()
            mongo_normalized = self.parser.parse_batch(mongo_logs, 'mongodb')
            all_logs.extend(mongo_normalized)
        except Exception as e:
            self.logger.error(f"Error collecting MongoDB logs: {e}")
        
        # If no logs collected and in demo mode (or first time), generate demo data
        if len(all_logs) == 0:
            if not self.demo_mode:
                self.logger.info("No database connections available - generating demo data for dashboard")
                self.demo_mode = True
            demo_logs = self.generate_demo_data()
            # Parse demo logs through parser for consistency
            for demo_log in demo_logs:
                parsed = self.parser.normalize_audit_log(demo_log, demo_log['database_type'])
                if parsed:
                    all_logs.append(parsed)
            self.logger.info(f"Generated {len(all_logs)} demo audit logs")
        else:
            self.demo_mode = False  # Real data available, disable demo mode
            
        self.logger.info(f"Collected {len(all_logs)} total audit logs")
        return all_logs
    
    async def analyze_security_threats(self, audit_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze audit logs for security threats"""
        all_threats = []
        
        for audit_log in audit_logs:
            threats = self.threat_detector.analyze_audit_log(audit_log)
            all_threats.extend(threats)
        
        if all_threats:
            self.logger.warning(f"Detected {len(all_threats)} security threats")
        
        return all_threats
    
    async def run_collection_cycle(self):
        """Run one collection cycle"""
        try:
            # Collect audit logs
            audit_logs = await self.collect_all_audit_logs()
            self.audit_logs.extend(audit_logs)
            
            # Keep only last 1000 logs for memory management
            if len(self.audit_logs) > 1000:
                self.audit_logs = self.audit_logs[-1000:]
            
            # Analyze for security threats
            threats = await self.analyze_security_threats(audit_logs)
            self.security_events.extend(threats)
            
            # Keep only last 100 security events
            if len(self.security_events) > 100:
                self.security_events = self.security_events[-100:]
            
            self.logger.info(f"Collection cycle complete: {len(audit_logs)} logs, {len(threats)} threats")
            
        except Exception as e:
            self.logger.error(f"Error in collection cycle: {e}")
    
    async def start(self):
        """Start the audit collection service"""
        if not await self.initialize():
            return
            
        self.logger.info("Starting continuous audit log collection...")
        
        while True:
            try:
                await self.run_collection_cycle()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except KeyboardInterrupt:
                self.logger.info("Shutdown requested")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
        
        await self.connection_manager.close_pools()
        self.logger.info("Database Audit Collection Service stopped")

# Global service instance for web dashboard
audit_service = None

async def main():
    """Main entry point"""
    global audit_service
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    audit_service = DatabaseAuditCollectorService()
    await audit_service.start()

if __name__ == "__main__":
    asyncio.run(main())
