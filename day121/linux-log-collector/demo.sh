#!/bin/bash
set -e

echo "🎬 Linux Log Collector Demo"
echo "=========================="

# Activate virtual environment
source venv/bin/activate

# Start collector in background
echo "🚀 Starting collector..."
python -m src.collector.main &
COLLECTOR_PID=$!

# Wait for startup
sleep 3

# Create demo log entries
echo "📝 Generating demo logs..."
mkdir -p data/demo_logs

# Create various log files
cat > data/demo_logs/syslog << 'DEMO_EOF'
Jan 15 10:15:00 server01 systemd[1]: Started application service
Jan 15 10:15:01 server01 kernel: CPU0: temperature above threshold
Jan 15 10:15:02 server01 nginx[1234]: 192.168.1.100 GET /api/users 200
DEMO_EOF

cat > data/demo_logs/auth.log << 'DEMO_EOF'  
Jan 15 10:15:00 server01 sshd[5678]: Accepted password for user from 192.168.1.200
Jan 15 10:15:01 server01 sudo: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/bin/ls
DEMO_EOF

echo "✅ Demo logs created!"
echo ""
echo "📊 Dashboard available at: http://localhost:8000"
echo "🔍 Check the dashboard to see log collection in action"
echo ""
echo "📈 Real-time statistics:"

# Show stats for 30 seconds
for i in {1..10}; do
    sleep 3
    echo "  ⏱️  $((i*3))s: Checking collector status..."
    curl -s http://localhost:8000/api/stats | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    stats = data.get('stats', {})
    print(f\"    📁 Discovery: {stats.get('discovery', {}).get('total_sources', 0)} sources\")
    print(f\"    👁️  Monitor: {stats.get('monitor', {}).get('monitored_files', 0)} files\")
    print(f\"    📦 Processor: {stats.get('processor', {}).get('batches_received', 0)} batches\")
except:
    print('    ⏳ Collector starting up...')
"
done

echo ""
echo "✅ Demo completed!"
echo "🛑 Stopping collector..."
kill $COLLECTOR_PID

echo "📚 Summary:"
echo "  - Discovered and monitored log files"
echo "  - Processed log entries in real-time"
echo "  - Displayed statistics on web dashboard"
echo "  - Demonstrated structured log collection"
