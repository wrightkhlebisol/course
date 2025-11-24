#!/bin/bash
# Generate active demo data that changes over time

set -e

echo "🎬 Starting Active Demo Data Generator"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Generate new log entries every 15 seconds"
echo "  2. Trigger exports every 30 seconds"
echo "  3. Show changing metrics on the dashboard"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Activate virtual environment
source venv/bin/activate

# Set AWS credentials
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-minioadmin}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-minioadmin}

# Counter for tracking
EXPORT_COUNT=0

# Function to generate new log data
generate_logs() {
    python3 << 'PYTHON_SCRIPT'
import sqlite3
from datetime import datetime, timedelta
import random
import json

conn = sqlite3.connect('data/logs.db')
cursor = conn.cursor()

services = ['api-gateway', 'auth-service', 'payment-service', 'user-service', 'notification-service']
levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
messages = [
    'Request processed successfully',
    'Authentication failed',
    'Payment transaction completed',
    'User session created',
    'Email notification sent',
    'Database query slow',
    'Cache miss occurred',
    'Rate limit exceeded',
    'New user registered',
    'Password reset requested',
    'API rate limit hit',
    'Cache updated',
    'Database connection pool exhausted',
    'External API call failed',
    'Session expired'
]

# Generate 50-100 new log entries
num_logs = random.randint(50, 100)
now = datetime.utcnow()

print(f"📝 Generating {num_logs} new log entries...")

for i in range(num_logs):
    timestamp = now - timedelta(seconds=random.randint(0, 60))
    service = random.choice(services)
    level = random.choice(levels)
    message = random.choice(messages)
    metadata = json.dumps({
        'user_id': random.randint(1000, 9999),
        'request_id': f'req-{random.randint(100000, 999999)}',
        'duration_ms': random.randint(10, 500)
    })
    
    cursor.execute("""
        INSERT INTO logs (timestamp, service, level, message, metadata)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, service, level, message, metadata))

conn.commit()
conn.close()

print(f"✅ Generated {num_logs} log entries")
PYTHON_SCRIPT
}

# Function to trigger export
trigger_export() {
    EXPORT_COUNT=$((EXPORT_COUNT + 1))
    echo ""
    echo "🚀 [Export #$EXPORT_COUNT] Triggering export at $(date '+%H:%M:%S')..."
    
    response=$(curl -s -X POST http://localhost:8000/api/export/manual \
        -H "Content-Type: application/json" \
        -d '{}')
    
    records=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin).get('records_exported', 0))")
    
    if [ "$records" -gt 0 ]; then
        echo "   ✅ Exported $records records"
    else
        echo "   ℹ️  No new records to export"
    fi
}

# Main loop
echo "⏰ Starting data generation cycle..."
echo ""

while true; do
    # Generate new logs
    generate_logs
    
    # Every 2nd cycle (30 seconds), trigger an export
    if [ $((EXPORT_COUNT % 2)) -eq 0 ]; then
        trigger_export
    fi
    
    echo "⏳ Waiting 15 seconds before next cycle..."
    sleep 15
done

