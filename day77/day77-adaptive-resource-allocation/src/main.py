#!/usr/bin/env python3

import sys
import signal
import time
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.adaptive_allocator import AdaptiveResourceAllocator
from ui.dashboard import app, socketio, set_allocator, start_real_time_updates

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutdown signal received")
    if hasattr(signal_handler, 'allocator'):
        signal_handler.allocator.stop()
    sys.exit(0)

def main():
    """Main application entry point"""
    print("🚀 Starting Adaptive Resource Allocation System")
    print("=" * 50)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Initialize allocator
        allocator = AdaptiveResourceAllocator()
        signal_handler.allocator = allocator
        
        # Set allocator for dashboard
        set_allocator(allocator)
        
        # Start allocator
        allocator.start()
        
        # Start real-time updates
        start_real_time_updates()
        
        print("\n✅ System started successfully!")
        print("🌐 Dashboard available at: http://localhost:8080")
        print("📊 Metrics collection active")
        print("🎯 Adaptive scaling enabled")
        print("\nPress Ctrl+C to stop...")
        
        # Start web dashboard
        socketio.run(app, debug=False, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        return 1
    finally:
        if hasattr(signal_handler, 'allocator'):
            signal_handler.allocator.stop()
            
    return 0

if __name__ == '__main__':
    exit(main())
