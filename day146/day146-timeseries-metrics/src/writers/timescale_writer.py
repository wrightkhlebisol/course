"""
Batch Writer for TimescaleDB - Efficiently writes metrics with batching
"""
import asyncio
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2.pool import ThreadedConnectionPool
from typing import List, Dict
from datetime import datetime
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetricBatch:
    metrics: List[Dict]
    max_size: int = 1000
    flush_interval: float = 2.0  # seconds

class TimescaleWriter:
    """Batched writer for TimescaleDB with connection pooling"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.connection_pool = None
        self.batch = []
        self.batch_size = 1000
        self.flush_interval = 2.0
        self.last_flush = datetime.now()
        self.total_written = 0
        self._setup_connection_pool()
    
    def _setup_connection_pool(self):
        """Create connection pool"""
        try:
            self.connection_pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'metrics'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', 'password')
            )
            logger.info("✅ Connection pool created")
        except Exception as e:
            logger.error(f"❌ Failed to create connection pool: {e}")
            raise
    
    def setup_schema(self):
        """Create hypertables for metrics"""
        conn = self.connection_pool.getconn()
        try:
            cur = conn.cursor()
            
            # Create extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            
            # HTTP response metrics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS http_response (
                    time TIMESTAMPTZ NOT NULL,
                    service TEXT NOT NULL,
                    component TEXT,
                    endpoint TEXT,
                    response_time_ms DOUBLE PRECISION,
                    host TEXT
                );
            """)
            
            # Convert to hypertable
            cur.execute("""
                SELECT create_hypertable('http_response', 'time', 
                    if_not_exists => TRUE, 
                    chunk_time_interval => INTERVAL '1 day');
            """)
            
            # HTTP status metrics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS http_status (
                    time TIMESTAMPTZ NOT NULL,
                    service TEXT NOT NULL,
                    component TEXT,
                    endpoint TEXT,
                    status_code INTEGER,
                    is_error INTEGER,
                    host TEXT
                );
            """)
            
            cur.execute("""
                SELECT create_hypertable('http_status', 'time', 
                    if_not_exists => TRUE, 
                    chunk_time_interval => INTERVAL '1 day');
            """)
            
            # Resource usage metrics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resource_usage (
                    time TIMESTAMPTZ NOT NULL,
                    service TEXT NOT NULL,
                    component TEXT,
                    cpu_percent DOUBLE PRECISION,
                    memory_mb DOUBLE PRECISION,
                    host TEXT
                );
            """)
            
            cur.execute("""
                SELECT create_hypertable('resource_usage', 'time', 
                    if_not_exists => TRUE, 
                    chunk_time_interval => INTERVAL '1 day');
            """)
            
            # Throughput metrics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS throughput (
                    time TIMESTAMPTZ NOT NULL,
                    service TEXT NOT NULL,
                    component TEXT,
                    request_count DOUBLE PRECISION,
                    host TEXT
                );
            """)
            
            cur.execute("""
                SELECT create_hypertable('throughput', 'time', 
                    if_not_exists => TRUE, 
                    chunk_time_interval => INTERVAL '1 day');
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_http_response_service ON http_response (service, time DESC);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_http_status_service ON http_status (service, time DESC);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_resource_service ON resource_usage (service, time DESC);")
            
            # Set up retention policy (7 days for raw data)
            cur.execute("""
                SELECT add_retention_policy('http_response', INTERVAL '7 days', if_not_exists => TRUE);
            """)
            cur.execute("""
                SELECT add_retention_policy('http_status', INTERVAL '7 days', if_not_exists => TRUE);
            """)
            
            conn.commit()
            logger.info("✅ Schema setup complete")
            
        except Exception as e:
            logger.error(f"❌ Schema setup failed: {e}")
            conn.rollback()
            raise
        finally:
            self.connection_pool.putconn(conn)
    
    def add_metric(self, metric: Dict):
        """Add metric to batch"""
        self.batch.append(metric)
        
        # Check if should flush
        if len(self.batch) >= self.batch_size:
            self.flush()
        elif (datetime.now() - self.last_flush).total_seconds() >= self.flush_interval:
            self.flush()
    
    def flush(self):
        """Write batched metrics to database"""
        if not self.batch:
            return
        
        conn = self.connection_pool.getconn()
        try:
            cur = conn.cursor()
            
            # Group by measurement type
            http_response = []
            http_status = []
            resource_usage = []
            throughput_data = []
            
            for metric in self.batch:
                measurement = metric.get('measurement')
                tags = metric.get('tags', {})
                fields = metric.get('fields', {})
                timestamp = metric.get('timestamp')
                
                if measurement == 'http_response':
                    http_response.append((
                        timestamp,
                        tags.get('service'),
                        tags.get('component'),
                        tags.get('endpoint'),
                        fields.get('response_time_ms'),
                        tags.get('host')
                    ))
                elif measurement == 'http_status':
                    http_status.append((
                        timestamp,
                        tags.get('service'),
                        tags.get('component'),
                        tags.get('endpoint'),
                        int(fields.get('status_code', 0)),
                        int(fields.get('is_error', 0)),
                        tags.get('host')
                    ))
                elif measurement == 'resource_usage':
                    resource_usage.append((
                        timestamp,
                        tags.get('service'),
                        tags.get('component'),
                        fields.get('cpu_percent'),
                        fields.get('memory_mb'),
                        tags.get('host')
                    ))
                elif measurement == 'throughput':
                    throughput_data.append((
                        timestamp,
                        tags.get('service'),
                        tags.get('component'),
                        fields.get('request_count'),
                        tags.get('host')
                    ))
            
            # Batch insert
            if http_response:
                execute_batch(cur, """
                    INSERT INTO http_response (time, service, component, endpoint, response_time_ms, host)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, http_response)
            
            if http_status:
                execute_batch(cur, """
                    INSERT INTO http_status (time, service, component, endpoint, status_code, is_error, host)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, http_status)
            
            if resource_usage:
                execute_batch(cur, """
                    INSERT INTO resource_usage (time, service, component, cpu_percent, memory_mb, host)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, resource_usage)
            
            if throughput_data:
                execute_batch(cur, """
                    INSERT INTO throughput (time, service, component, request_count, host)
                    VALUES (%s, %s, %s, %s, %s)
                """, throughput_data)
            
            conn.commit()
            self.total_written += len(self.batch)
            logger.info(f"✅ Flushed {len(self.batch)} metrics (total: {self.total_written})")
            
            self.batch = []
            self.last_flush = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Flush failed: {e}")
            conn.rollback()
            raise
        finally:
            self.connection_pool.putconn(conn)
    
    def close(self):
        """Flush remaining metrics and close connections"""
        self.flush()
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("✅ Connection pool closed")

if __name__ == '__main__':
    # Test writer
    writer = TimescaleWriter({
        'host': 'localhost',
        'port': 5432,
        'database': 'metrics',
        'user': 'postgres',
        'password': 'password'
    })
    
    try:
        writer.setup_schema()
        print("✅ Writer test complete")
    except Exception as e:
        print(f"❌ Writer test failed: {e}")
