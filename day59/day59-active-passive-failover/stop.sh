#!/bin/bash

# Day 59: Active-Passive Failover Stop Script
# 254-Day Hands-On System Design Series

set -e

PROJECT_NAME="day59-active-passive-failover"

echo "🛑 Stopping Active-Passive Failover System"
echo "=========================================="

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
if [ -f "docker-compose.yml" ]; then
    docker-compose down --remove-orphans
    echo "✅ Docker containers stopped"
else
    echo "⚠️  No docker-compose.yml found"
fi

# Stop any running Python processes
echo "🐍 Stopping Python processes..."
pkill -f "python.*failover" || true
pkill -f "python.*log_processor" || true
pkill -f "python.*main.py" || true
echo "✅ Python processes stopped"

# Stop any running Node.js processes
echo "📦 Stopping Node.js processes..."
pkill -f "node.*react" || true
pkill -f "npm.*start" || true
echo "✅ Node.js processes stopped"

# Stop any running nginx processes
echo "🌐 Stopping nginx processes..."
pkill -f "nginx" || true
echo "✅ nginx processes stopped"

# Stop Redis if running
echo "🔴 Stopping Redis..."
pkill -f "redis-server" || true
echo "✅ Redis stopped"

# Clean up any temporary files
echo "🧹 Cleaning up temporary files..."
rm -rf logs/*.log 2>/dev/null || true
rm -rf src/frontend/build 2>/dev/null || true
echo "✅ Temporary files cleaned"

# Stop any background tasks
echo "🔄 Stopping background tasks..."
jobs -p | xargs -r kill 2>/dev/null || true
echo "✅ Background tasks stopped"

# Check if any processes are still running
echo "🔍 Checking for remaining processes..."
REMAINING_PROCESSES=$(ps aux | grep -E "(failover|log_processor|react|nginx)" | grep -v grep || true)

if [ -n "$REMAINING_PROCESSES" ]; then
    echo "⚠️  Some processes may still be running:"
    echo "$REMAINING_PROCESSES"
    echo "💡 You may need to manually stop them with: kill -9 <PID>"
else
    echo "✅ All processes stopped successfully"
fi

echo ""
echo "🎉 Active-Passive Failover System stopped!"
echo ""
echo "📊 System Status:"
echo "  - Docker containers: STOPPED"
echo "  - Python processes: STOPPED" 
echo "  - Node.js processes: STOPPED"
echo "  - nginx processes: STOPPED"
echo "  - Redis: STOPPED"
echo ""
echo "🚀 To restart the system:"
echo "  ./scripts/demo.sh"
echo ""
echo "✅ Stop script completed successfully!" 