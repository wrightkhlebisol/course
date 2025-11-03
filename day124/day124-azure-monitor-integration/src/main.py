#!/usr/bin/env python3
"""
Azure Monitor Integration - Main Application
Day 124 of 254-Day System Design Series
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from dashboard.app import app
from azure_monitor.connector import AzureMonitorConnector
from azure_monitor.processor import AzureLogProcessor
from config.azure_config import DEMO_CONFIG

async def test_azure_connection():
    """Test Azure Monitor connection"""
    print("🔍 Testing Azure Monitor connection...")
    
    connector = AzureMonitorConnector(DEMO_CONFIG)
    
    # Test connection
    connected = await connector.connect()
    if connected:
        print("✅ Azure Monitor connection successful!")
        
        # Discover workspaces
        workspaces = await connector.discover_workspaces()
        print(f"📊 Discovered {len(workspaces)} workspaces:")
        for ws in workspaces:
            print(f"  - {ws['name']} ({ws['id']})")
        
        # Test log collection
        print("📝 Testing log collection...")
        processor = AzureLogProcessor()
        
        log_count = 0
        async for log_entry in connector.query_logs(workspaces[0]['id']):
            await processor.process_log_entry(log_entry)
            log_count += 1
            if log_count >= 5:  # Test with first 5 logs
                break
        
        print(f"✅ Successfully processed {log_count} log entries")
        
        # Show statistics
        stats = processor.get_statistics()
        print(f"📈 Statistics: {stats}")
        
    else:
        print("❌ Azure Monitor connection failed!")
    
    await connector.close()
    return connected

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Run connection test
            asyncio.run(test_azure_connection())
        elif sys.argv[1] == "web":
            # Start web dashboard
            import uvicorn
            print("🌐 Starting Azure Monitor Dashboard...")
            print("📊 Dashboard URL: http://localhost:8000")
            uvicorn.run(app, host="0.0.0.0", port=8000)
        else:
            print("Usage: python main.py [test|web]")
    else:
        print("🚀 Azure Monitor Integration")
        print("Commands:")
        print("  python main.py test  - Test Azure connection")
        print("  python main.py web   - Start web dashboard")

if __name__ == "__main__":
    main()
