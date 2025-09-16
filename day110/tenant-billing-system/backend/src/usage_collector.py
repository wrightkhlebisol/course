import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
from models import UsageMetric
import threading
import random

class UsageCollector:
    def __init__(self, db_path: str = "usage.db"):
        self.db_path = db_path
        self.init_database()
        self._running = False
        self._thread = None
        
    def init_database(self):
        """Initialize SQLite database for usage tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create usage metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                bytes_ingested INTEGER DEFAULT 0,
                storage_used INTEGER DEFAULT 0,
                queries_processed INTEGER DEFAULT 0,
                compute_seconds REAL DEFAULT 0,
                bandwidth_gb REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create tenants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tier TEXT DEFAULT 'starter',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def record_usage(self, usage: UsageMetric) -> bool:
        """Record usage metrics for a tenant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO usage_metrics 
                (tenant_id, timestamp, bytes_ingested, storage_used, 
                 queries_processed, compute_seconds, bandwidth_gb)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                usage.tenant_id,
                usage.timestamp.isoformat(),
                usage.bytes_ingested,
                usage.storage_used,
                usage.queries_processed,
                usage.compute_seconds,
                usage.bandwidth_gb
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error recording usage: {e}")
            return False
            
    def get_usage_for_period(self, tenant_id: str, start_date: datetime, 
                           end_date: datetime) -> List[Dict]:
        """Get usage metrics for a tenant within a date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM usage_metrics 
            WHERE tenant_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (tenant_id, start_date.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'tenant_id', 'timestamp', 'bytes_ingested', 
                  'storage_used', 'queries_processed', 'compute_seconds', 
                  'bandwidth_gb', 'created_at']
        
        return [dict(zip(columns, row)) for row in rows]
        
    def simulate_usage_data(self):
        """Generate realistic usage data for demo purposes"""
        tenants = ['tenant_1', 'tenant_2', 'tenant_3', 'tenant_enterprise']
        
        while self._running:
            for tenant in tenants:
                # Simulate varying usage patterns
                base_bytes = 1000000 if 'enterprise' in tenant else 50000
                bytes_variation = random.randint(-20000, 100000)
                
                usage = UsageMetric(
                    tenant_id=tenant,
                    timestamp=datetime.now(),
                    bytes_ingested=max(0, base_bytes + bytes_variation),
                    storage_used=random.randint(500000, 5000000),
                    queries_processed=random.randint(10, 500),
                    compute_seconds=random.uniform(0.1, 10.0),
                    bandwidth_gb=random.uniform(0.01, 1.0)
                )
                
                self.record_usage(usage)
            
            time.sleep(10)  # Collect metrics every 10 seconds
            
    def start_simulation(self):
        """Start usage data simulation in background"""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self.simulate_usage_data)
            self._thread.start()
            
    def stop_simulation(self):
        """Stop usage data simulation"""
        if self._running:
            self._running = False
            if self._thread:
                self._thread.join()
                
    def get_current_usage(self, tenant_id: str) -> Dict:
        """Get current usage summary for a tenant"""
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        usage_data = self.get_usage_for_period(tenant_id, start_of_day, now)
        
        total_bytes = sum(row['bytes_ingested'] for row in usage_data)
        total_storage = max((row['storage_used'] for row in usage_data), default=0)
        total_queries = sum(row['queries_processed'] for row in usage_data)
        total_compute = sum(row['compute_seconds'] for row in usage_data)
        
        return {
            'tenant_id': tenant_id,
            'daily_bytes_ingested': total_bytes,
            'current_storage_used': total_storage,
            'daily_queries_processed': total_queries,
            'daily_compute_seconds': total_compute,
            'data_points': len(usage_data),
            'last_updated': now.isoformat()
        }
