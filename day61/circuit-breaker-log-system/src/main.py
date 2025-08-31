"""
Main application entry point for circuit breaker system
"""
import sys
import asyncio
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, '.')

from monitoring.dashboard import app, monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("Starting Circuit Breaker System")
    logger.info(f"System started at: {datetime.now()}")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # Start web dashboard
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Run interactive demo
        run_demo()

def run_demo():
    """Run interactive demonstration"""
    from services.log_processor import LogProcessorService
    from circuit_breaker.core import registry
    
    processor = LogProcessorService()
    
    print("🚀 Circuit Breaker System Demo")
    print("=" * 50)
    
    # Process some test logs
    print("\n1. Processing test logs...")
    test_logs = [
        {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': f'Test log message {i}',
            'service': f'test-service-{i % 3}',
            'user_id': f'user_{i}'
        }
        for i in range(10)
    ]
    
    for log in test_logs:
        result = processor.process_log(log)
        print(f"  ✓ Processed log {result['original_log']['message']}")
    
    # Show circuit breaker stats
    print("\n2. Circuit Breaker Statistics:")
    stats = registry.get_all_stats()
    for name, cb_stats in stats['circuit_breakers'].items():
        print(f"  {name}: {cb_stats['state']} - {cb_stats['success_rate']}% success rate")
    
    # Simulate failures
    print("\n3. Simulating failures...")
    processor.database.set_failure_rate(0.8)
    processor.external_api.set_down(True)
    
    # Process more logs with failures
    for i in range(5):
        log = {
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': f'Failure test log {i}',
            'service': 'failing-service'
        }
        result = processor.process_log(log)
        print(f"  ⚠️  Processed with fallbacks: {len(result['fallbacks_used'])}")
    
    # Show updated stats
    print("\n4. Updated Statistics:")
    stats = registry.get_all_stats()
    for name, cb_stats in stats['circuit_breakers'].items():
        print(f"  {name}: {cb_stats['state']} - {cb_stats['success_rate']}% success rate")
    
    print("\n✅ Demo completed!")
    print("💡 Run 'python src/main.py web' to start the web dashboard")

if __name__ == "__main__":
    main()
