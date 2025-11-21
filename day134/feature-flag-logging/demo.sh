#!/bin/bash

set -e

echo "🎬 Feature Flag Status Logging System Demo"
echo "========================================"

# Check if services are running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend not running. Please run ./start.sh first."
    exit 1
fi

echo "🎯 Creating demo feature flags..."

# Create sample flags
curl -s -X POST http://localhost:8000/api/v1/flags \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dark_mode",
    "description": "Enable dark mode for the application",
    "enabled": true,
    "rollout_percentage": "50",
    "target_groups": ["beta-users", "premium-users"]
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/v1/flags \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_checkout",
    "description": "New checkout flow with improved UX",
    "enabled": false,
    "rollout_percentage": "10",
    "target_groups": ["internal-users"]
  }' > /dev/null

curl -s -X POST http://localhost:8000/api/v1/flags \
  -H "Content-Type: application/json" \
  -d '{
    "name": "analytics_tracking",
    "description": "Enhanced analytics tracking",
    "enabled": true,
    "rollout_percentage": "100"
  }' > /dev/null

echo "✅ Created demo feature flags"

echo "🔄 Simulating flag evaluations..."

# Simulate flag evaluations
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/flags/evaluate \
    -H "Content-Type: application/json" \
    -d "{
      \"flag_name\": \"dark_mode\",
      \"user_context\": {\"user_id\": \"user_$i\", \"group\": \"beta-users\"},
      \"default_value\": false
    }" > /dev/null
done

echo "✅ Simulated 10 flag evaluations"

echo "🔧 Simulating flag updates..."

# Get dark_mode flag ID and update it
FLAG_ID=$(curl -s http://localhost:8000/api/v1/flags | jq -r '.[] | select(.name=="dark_mode") | .id')

curl -s -X PUT http://localhost:8000/api/v1/flags/$FLAG_ID \
  -H "Content-Type: application/json" \
  -d '{
    "rollout_percentage": "75",
    "description": "Enable dark mode for the application - Updated rollout"
  }' > /dev/null

echo "✅ Updated dark_mode flag rollout to 75%"

echo "📊 Fetching recent activity..."
curl -s http://localhost:8000/api/v1/logs/recent | jq '.[0:5] | .[] | {flag_name, event_type, timestamp}'

echo ""
echo "🎉 Demo completed successfully!"
echo ""
echo "🌐 Open these URLs to explore:"
echo "  • Frontend Dashboard: http://localhost:3000"
echo "  • Backend API Docs: http://localhost:8000/docs"
echo "  • Recent Logs: http://localhost:8000/api/v1/logs/recent"
