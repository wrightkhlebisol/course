#!/usr/bin/env python3
"""
Main entry point for the distributed tracing system
"""
import asyncio
import multiprocessing
import subprocess
import sys
import time
import signal
from pathlib import Path

def start_service(service_module, port):
    """Start a service in a separate process"""
    import uvicorn
    uvicorn.run(
        service_module,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

def start_redis():
    """Start Redis server if not running"""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, socket_timeout=1)
        client.ping()
        print("✅ Redis is already running")
        return None
    except:
        print("🚀 Starting Redis server...")
        try:
            process = subprocess.Popen(
                ["redis-server", "--daemonize", "yes"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)  # Give Redis time to start
            return process
        except FileNotFoundError:
            print("❌ Redis not found. Please install Redis server")
            print("   Ubuntu/Debian: sudo apt-get install redis-server")
            print("   macOS: brew install redis")
            print("   Or run: docker run -d -p 6379:6379 redis:alpine")
            return None

def main():
    """Main function to start all services"""
    print("🚀 Starting Distributed Tracing System")
    print("=" * 50)
    
    # Start Redis
    redis_process = start_redis()
    
    # Import configurations
    from config.config import service_config, config
    
    # Service configurations
    services = [
        ("src.services.api_gateway:app", service_config.api_gateway_port, "API Gateway"),
        ("src.services.user_service:app", service_config.user_service_port, "User Service"),
        ("src.services.database_service:app", service_config.database_service_port, "Database Service"),
        ("src.dashboard.dashboard:app", config.dashboard_port, "Tracing Dashboard")
    ]
    
    processes = []
    
    try:
        # Start all services
        for service_module, port, name in services:
            print(f"🚀 Starting {name} on port {port}")
            process = multiprocessing.Process(
                target=start_service,
                args=(service_module, port)
            )
            process.start()
            processes.append((process, name))
            time.sleep(1)  # Stagger startup
        
        print("\n✅ All services started successfully!")
        print(f"🌐 Dashboard: http://localhost:{config.dashboard_port}")
        print(f"🔌 API Gateway: http://localhost:{service_config.api_gateway_port}")
        print(f"👤 User Service: http://localhost:{service_config.user_service_port}")
        print(f"💾 Database Service: http://localhost:{service_config.database_service_port}")
        print("\n📖 Check README.md for API usage examples")
        print("🛑 Press Ctrl+C to stop all services")
        
        # Wait for interrupt
        signal.signal(signal.SIGINT, lambda s, f: None)
        signal.pause()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
    finally:
        # Terminate all processes
        for process, name in processes:
            if process.is_alive():
                print(f"🛑 Stopping {name}")
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        
        if redis_process:
            redis_process.terminate()
        
        print("✅ All services stopped")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run in test mode
        from tests.run_tests import run_all_tests
        run_all_tests()
    else:
        main()
