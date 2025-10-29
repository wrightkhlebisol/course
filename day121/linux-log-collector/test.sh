#!/bin/bash
set -e

echo "🧪 Running functional tests..."

# Activate virtual environment
source venv/bin/activate

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/ -v

# Create test log files
echo "Creating test log files..."
mkdir -p data/test_logs
echo "$(date) - Test syslog entry" >> data/test_logs/test.log
echo "$(date) - Test auth entry" >> data/test_logs/auth.log

# Test discovery
echo "Testing discovery engine..."
python -c "
import asyncio
import sys
sys.path.append('src')
from collector.discovery.log_discovery import LogDiscoveryEngine

async def test():
    config = {
        'discovery': {
            'scan_paths': ['data/test_logs'],
            'exclude_patterns': ['*.backup']
        }
    }
    engine = LogDiscoveryEngine(config)
    await engine.discover_sources()
    sources = engine.get_discovered_sources()
    print(f'✅ Discovered {len(sources)} test sources')
    for path in sources:
        print(f'  - {path}')

asyncio.run(test())
"

echo "✅ All tests passed!"
