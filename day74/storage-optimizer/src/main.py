"""
Storage Format Optimization System - Main Application
"""
import asyncio
import uvicorn
from storage.storage_engine import AdaptiveStorageEngine
from analyzer.pattern_analyzer import AccessPatternAnalyzer
from web.dashboard import StorageOptimizationDashboard
from datetime import datetime
import json
import random

class StorageOptimizationSystem:
    def __init__(self):
        self.storage_engine = AdaptiveStorageEngine("data")
        self.pattern_analyzer = AccessPatternAnalyzer()
        self.dashboard = StorageOptimizationDashboard(self.storage_engine, self.pattern_analyzer)
        
    async def start(self):
        """Start the optimization system"""
        print("🚀 Starting Storage Format Optimization System")
        print("=" * 50)
        
        # Generate sample data for demonstration
        await self.generate_demo_data()
        
        # Start the web dashboard
        print("🌐 Starting web dashboard...")
        config = uvicorn.Config(
            app=self.dashboard.app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        print("✅ Storage Optimization System ready!")
        print("📊 Dashboard: http://localhost:8000")
        print("🔄 System will continuously optimize storage formats...")
        
        await server.serve()
    
    async def generate_demo_data(self):
        """Generate demonstration data with different query patterns"""
        print("📝 Generating demonstration data...")
        
        # Sample log entries with realistic structure
        sample_logs = []
        services = ['web-api', 'user-service', 'payment-service', 'analytics']
        log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        
        for i in range(100):
            log_entry = {
                'id': f"log_{i:04d}",
                'timestamp': datetime.now().isoformat(),
                'service': random.choice(services),
                'level': random.choice(log_levels),
                'message': f"Sample log message {i}",
                'user_id': f"user_{random.randint(1, 1000):04d}",
                'request_id': f"req_{random.randint(1, 10000):06d}",
                'duration_ms': random.randint(10, 2000),
                'status_code': random.choice([200, 201, 400, 404, 500]),
                'ip_address': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                'metadata': {
                    'region': random.choice(['us-west-1', 'us-east-1', 'eu-west-1']),
                    'version': f"v{random.randint(1, 5)}.{random.randint(0, 10)}",
                    'environment': random.choice(['prod', 'staging', 'dev'])
                }
            }
            sample_logs.append(log_entry)
        
        # Write logs to different partitions
        partitions = ['web-logs', 'api-logs', 'error-logs']
        for partition in partitions:
            partition_logs = sample_logs[:30]  # Use subset for each partition
            await self.storage_engine.write_logs(partition_logs, partition)
        
        # Simulate different query patterns
        await self.simulate_query_patterns()
        
        print(f"✅ Generated {len(sample_logs)} demo logs across {len(partitions)} partitions")
    
    async def simulate_query_patterns(self):
        """Simulate different query patterns to trigger format optimization"""
        print("🔍 Simulating query patterns...")
        
        # Pattern 1: Full record queries (row-oriented friendly)
        for i in range(10):
            query = {'level': 'ERROR'}
            results = await self.storage_engine.read_logs(query, 'error-logs')
            self.pattern_analyzer.record_query(
                'error-logs', query, 0.05, len(results)
            )
        
        # Pattern 2: Analytical queries (columnar friendly)
        for i in range(20):
            query = {
                'columns': ['timestamp', 'duration_ms', 'status_code'],
                'aggregation': True
            }
            results = await self.storage_engine.read_logs(query, 'api-logs')
            self.pattern_analyzer.record_query(
                'api-logs', query, 0.15, len(results)
            )
        
        # Pattern 3: Mixed queries (hybrid friendly)
        for i in range(15):
            query = {
                'service': 'web-api',
                'columns': ['timestamp', 'message', 'user_id', 'status_code']
            }
            results = await self.storage_engine.read_logs(query, 'web-logs')
            self.pattern_analyzer.record_query(
                'web-logs', query, 0.08, len(results)
            )
        
        print("✅ Query pattern simulation completed")

async def main():
    system = StorageOptimizationSystem()
    await system.start()

if __name__ == "__main__":
    asyncio.run(main())
