#!/bin/bash
set -e

echo "🎬 Day 146 Demo: Time Series Metrics System"
echo "============================================"
echo ""

# Activate venv
source venv/bin/activate

# Check if TimescaleDB is running
echo "1️⃣  Checking TimescaleDB connection..."
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='metrics',
        user='postgres',
        password='password'
    )
    conn.close()
    print('   ✅ TimescaleDB connected')
except Exception as e:
    print('   ❌ TimescaleDB not available. Start with: docker-compose up -d timescaledb')
    exit(1)
"

# Setup schema
echo ""
echo "2️⃣  Setting up database schema..."
python -c "
from src.writers.timescale_writer import TimescaleWriter
writer = TimescaleWriter({
    'host': 'localhost',
    'port': 5432,
    'database': 'metrics',
    'user': 'postgres',
    'password': 'password'
})
writer.setup_schema()
writer.close()
print('   ✅ Schema created')
"

# Generate and process logs
echo ""
echo "3️⃣  Generating and processing test logs..."
python -c "
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
import asyncio
from main import MetricsPipeline

async def demo():
    pipeline = MetricsPipeline()
    pipeline.setup()
    print('   🔄 Processing logs for 30 seconds...')
    await pipeline.process_logs(duration=30)
    pipeline.stop()
    print('   ✅ Log processing complete')

asyncio.run(demo())
"

# Query metrics
echo ""
echo "4️⃣  Querying metrics from TimescaleDB..."
python -c "
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='metrics',
    user='postgres',
    password='password',
    cursor_factory=RealDictCursor
)
cur = conn.cursor()

# Response time metrics
cur.execute('''
    SELECT 
        service,
        COUNT(*) as count,
        AVG(response_time_ms) as avg_response_time,
        MIN(response_time_ms) as min_response_time,
        MAX(response_time_ms) as max_response_time
    FROM http_response
    GROUP BY service
    ORDER BY service;
''')

print('   📊 Response Time Metrics:')
for row in cur.fetchall():
    print(f\"      {row['service']}: {row['avg_response_time']:.2f}ms avg (min: {row['min_response_time']:.2f}, max: {row['max_response_time']:.2f}, count: {row['count']})\")

# Error rates
cur.execute('''
    SELECT 
        service,
        COUNT(*) as total,
        SUM(is_error) as errors,
        (SUM(is_error)::float / COUNT(*)::float * 100) as error_rate
    FROM http_status
    GROUP BY service
    ORDER BY service;
''')

print('   🚨 Error Rate Metrics:')
for row in cur.fetchall():
    print(f\"      {row['service']}: {row['error_rate']:.2f}% ({row['errors']}/{row['total']})\")

conn.close()
print('   ✅ Query complete')
"

echo ""
echo "5️⃣  Starting API and Dashboard..."
echo "   Run these commands in separate terminals:"
echo "   Terminal 1: uvicorn src.api.query_api:app --reload"
echo "   Terminal 2: cd src/dashboard && npm start"
echo ""
echo "   Then visit: http://localhost:3000"
echo ""
echo "✅ Demo complete!"
