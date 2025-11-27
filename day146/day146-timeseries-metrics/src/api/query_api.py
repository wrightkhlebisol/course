"""
Query API - REST endpoints for querying metrics from TimescaleDB
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Metrics Query API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration - read from environment variables with fallback to defaults
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'metrics'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def setup_schema():
    """Initialize database schema and hypertables"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create TimescaleDB extension
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
        
        conn.commit()
        conn.close()
        logger.info("✅ Database schema initialized")
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        # Don't raise - allow API to start even if schema setup fails
        # (schema might already exist)

@app.on_event("startup")
async def startup_event():
    """Initialize database schema on startup"""
    logger.info("🔧 Initializing database schema...")
    setup_schema()

@app.get("/")
async def root():
    return {"message": "Metrics Query API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/metrics/response-time")
async def get_response_time_metrics(
    service: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = Query(default="5m", regex="^[0-9]+(s|m|h)$")
):
    """Get response time metrics with time-bucket aggregation"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Default time range: last hour
        if not end_time:
            end_time = datetime.now().isoformat()
        if not start_time:
            start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        
        query = """
            SELECT 
                time_bucket(%s::interval, time) AS bucket,
                service,
                AVG(response_time_ms) as avg_response_time,
                MIN(response_time_ms) as min_response_time,
                MAX(response_time_ms) as max_response_time,
                percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
                COUNT(*) as sample_count
            FROM http_response
            WHERE time >= %s::timestamptz AND time <= %s::timestamptz
        """
        
        params = [interval, start_time, end_time]
        
        if service:
            query += " AND service = %s"
            params.append(service)
        
        query += " GROUP BY bucket, service ORDER BY bucket DESC LIMIT 100"
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        conn.close()
        
        return {
            "data": results,
            "meta": {
                "start_time": start_time,
                "end_time": end_time,
                "interval": interval,
                "count": len(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/error-rate")
async def get_error_rate(
    service: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = Query(default="5m", regex="^[0-9]+(s|m|h)$")
):
    """Get error rate metrics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if not end_time:
            end_time = datetime.now().isoformat()
        if not start_time:
            start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        
        query = """
            SELECT 
                time_bucket(%s::interval, time) AS bucket,
                service,
                COUNT(*) as total_requests,
                SUM(is_error) as error_count,
                (SUM(is_error)::float / COUNT(*)::float * 100) as error_rate
            FROM http_status
            WHERE time >= %s::timestamptz AND time <= %s::timestamptz
        """
        
        params = [interval, start_time, end_time]
        
        if service:
            query += " AND service = %s"
            params.append(service)
        
        query += " GROUP BY bucket, service ORDER BY bucket DESC LIMIT 100"
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        conn.close()
        
        return {
            "data": results,
            "meta": {
                "start_time": start_time,
                "end_time": end_time,
                "interval": interval
            }
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/resource-usage")
async def get_resource_usage(
    service: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Get resource usage metrics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if not end_time:
            end_time = datetime.now().isoformat()
        if not start_time:
            start_time = (datetime.now() - timedelta(minutes=30)).isoformat()
        
        query = """
            SELECT 
                time_bucket('1m', time) AS bucket,
                service,
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_mb) as avg_memory,
                MAX(memory_mb) as max_memory
            FROM resource_usage
            WHERE time >= %s::timestamptz AND time <= %s::timestamptz
        """
        
        params = [start_time, end_time]
        
        if service:
            query += " AND service = %s"
            params.append(service)
        
        query += " GROUP BY bucket, service ORDER BY bucket DESC LIMIT 100"
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        conn.close()
        
        return {
            "data": results,
            "meta": {
                "start_time": start_time,
                "end_time": end_time
            }
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/throughput")
async def get_throughput(
    service: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = Query(default="1m", regex="^[0-9]+(s|m|h)$")
):
    """Get throughput metrics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if not end_time:
            end_time = datetime.now().isoformat()
        if not start_time:
            start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        
        query = """
            SELECT 
                time_bucket(%s::interval, time) AS bucket,
                service,
                SUM(request_count) as total_requests,
                AVG(request_count) as avg_requests
            FROM throughput
            WHERE time >= %s::timestamptz AND time <= %s::timestamptz
        """
        
        params = [interval, start_time, end_time]
        
        if service:
            query += " AND service = %s"
            params.append(service)
        
        query += " GROUP BY bucket, service ORDER BY bucket DESC LIMIT 100"
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        conn.close()
        
        return {
            "data": results,
            "meta": {
                "start_time": start_time,
                "end_time": end_time,
                "interval": interval
            }
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/summary")
async def get_summary():
    """Get overall metrics summary"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Last hour summary
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        
        # Response time summary
        cur.execute("""
            SELECT 
                service,
                AVG(response_time_ms) as avg_response_time,
                percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
                COUNT(*) as request_count
            FROM http_response
            WHERE time >= %s::timestamptz
            GROUP BY service
        """, (one_hour_ago,))
        response_summary = cur.fetchall()
        
        # Error rate summary
        cur.execute("""
            SELECT 
                service,
                COUNT(*) as total_requests,
                SUM(is_error) as error_count,
                (SUM(is_error)::float / COUNT(*)::float * 100) as error_rate
            FROM http_status
            WHERE time >= %s::timestamptz
            GROUP BY service
        """, (one_hour_ago,))
        error_summary = cur.fetchall()
        
        conn.close()
        
        return {
            "response_time": response_summary,
            "error_rate": error_summary,
            "timeframe": "last_1_hour"
        }
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
