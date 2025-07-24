"""
Storage Format Optimization Demo
"""
import asyncio
import json
from datetime import datetime
import random
import time

# Add src to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage.storage_engine import AdaptiveStorageEngine
from analyzer.pattern_analyzer import AccessPatternAnalyzer

class StorageDemo:
    def __init__(self):
        self.storage_engine = AdaptiveStorageEngine("demo_data")
        self.pattern_analyzer = AccessPatternAnalyzer()
    
    async def run_demo(self):
        """Run comprehensive storage optimization demonstration"""
        print("🚀 Storage Format Optimization Demo")
        print("=" * 50)
        
        # Phase 1: Generate sample data
        await self.phase1_generate_data()
        
        # Phase 2: Demonstrate different query patterns
        await self.phase2_query_patterns()
        
        # Phase 3: Show optimization recommendations
        await self.phase3_optimization()
        
        # Phase 4: Performance comparison
        await self.phase4_performance()
        
        print("\n✅ Demo completed successfully!")
        print("🌐 Start the web dashboard with: python src/main.py")
    
    async def phase1_generate_data(self):
        """Generate realistic log data for demonstration"""
        print("\n📝 Phase 1: Generating Sample Data")
        print("-" * 30)
        
        # Create different types of log entries
        web_logs = []
        api_logs = []
        error_logs = []
        
        for i in range(200):
            timestamp = datetime.now().isoformat()
            
            # Web server logs
            web_log = {
                'id': f'web_{i:04d}',
                'timestamp': timestamp,
                'service': 'web-server',
                'level': random.choice(['INFO', 'DEBUG']),
                'method': random.choice(['GET', 'POST', 'PUT']),
                'path': random.choice(['/api/users', '/api/orders', '/health']),
                'status_code': random.choice([200, 201, 304, 404]),
                'response_time': random.randint(10, 500),
                'ip_address': f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                'user_agent': 'Mozilla/5.0...'
            }
            web_logs.append(web_log)
            
            # API logs
            if i % 3 == 0:
                api_log = {
                    'id': f'api_{i:04d}',
                    'timestamp': timestamp,
                    'service': 'payment-api',
                    'level': 'INFO',
                    'transaction_id': f'txn_{random.randint(1000, 9999)}',
                    'amount': random.randint(10, 1000),
                    'currency': 'USD',
                    'status': random.choice(['success', 'pending', 'failed']),
                    'processing_time': random.randint(50, 2000)
                }
                api_logs.append(api_log)
            
            # Error logs
            if i % 10 == 0:
                error_log = {
                    'id': f'error_{i:04d}',
                    'timestamp': timestamp,
                    'service': random.choice(['web-server', 'payment-api', 'user-service']),
                    'level': 'ERROR',
                    'error_code': random.choice(['E001', 'E002', 'E003']),
                    'error_message': 'Sample error message',
                    'stack_trace': 'Stack trace details...',
                    'affected_user': f'user_{random.randint(1, 100)}'
                }
                error_logs.append(error_log)
        
        # Store in different partitions
        await self.storage_engine.write_logs(web_logs, 'web-logs')
        await self.storage_engine.write_logs(api_logs, 'api-logs')
        await self.storage_engine.write_logs(error_logs, 'error-logs')
        
        print(f"✅ Generated {len(web_logs)} web logs")
        print(f"✅ Generated {len(api_logs)} API logs")
        print(f"✅ Generated {len(error_logs)} error logs")
    
    async def phase2_query_patterns(self):
        """Demonstrate different query patterns"""
        print("\n🔍 Phase 2: Demonstrating Query Patterns")
        print("-" * 40)
        
        # Pattern 1: Full record queries (row-oriented friendly)
        print("📋 Pattern 1: Full record access (row-oriented optimal)")
        start_time = time.time()
        
        for i in range(5):
            query = {'level': 'ERROR'}
            results = await self.storage_engine.read_logs(query, 'error-logs')
            self.pattern_analyzer.record_query('error-logs', query, 0.1, len(results))
        
        full_time = time.time() - start_time
        print(f"   ⏱️  5 full record queries: {full_time:.3f}s")
        
        # Pattern 2: Analytical queries (columnar friendly)
        print("📊 Pattern 2: Analytical access (columnar optimal)")
        start_time = time.time()
        
        for i in range(10):
            query = {
                'columns': ['timestamp', 'response_time', 'status_code'],
                'aggregation': True,
                'service': 'web-server'
            }
            results = await self.storage_engine.read_logs(query, 'web-logs')
            self.pattern_analyzer.record_query('web-logs', query, 0.2, len(results))
        
        analytical_time = time.time() - start_time
        print(f"   ⏱️  10 analytical queries: {analytical_time:.3f}s")
        
        # Pattern 3: Mixed queries (hybrid friendly)
        print("🔀 Pattern 3: Mixed access (hybrid optimal)")
        start_time = time.time()
        
        for i in range(8):
            if i % 2 == 0:
                query = {'transaction_id': f'txn_{random.randint(1000, 9999)}'}
            else:
                query = {'columns': ['amount', 'currency', 'status']}
            
            results = await self.storage_engine.read_logs(query, 'api-logs')
            self.pattern_analyzer.record_query('api-logs', query, 0.15, len(results))
        
        mixed_time = time.time() - start_time
        print(f"   ⏱️  8 mixed queries: {mixed_time:.3f}s")
    
    async def phase3_optimization(self):
        """Show optimization recommendations"""
        print("\n🎯 Phase 3: Storage Format Recommendations")
        print("-" * 45)
        
        partitions = ['error-logs', 'web-logs', 'api-logs']
        
        for partition in partitions:
            recommendations = self.pattern_analyzer.get_recommendations(partition)
            
            print(f"\n📊 Partition: {partition}")
            print(f"   Recommended Format: {recommendations['recommended_format'].upper()}")
            print(f"   Confidence: {recommendations['confidence'].upper()}")
            print(f"   Analytical Ratio: {recommendations['analytical_ratio']:.2f}")
            print(f"   Full Record Ratio: {recommendations['full_record_ratio']:.2f}")
            print(f"   Total Queries: {recommendations['total_queries']}")
    
    async def phase4_performance(self):
        """Show performance comparison"""
        print("\n⚡ Phase 4: Performance Analysis")
        print("-" * 35)
        
        # Get current system stats
        stats = self.storage_engine.get_optimization_stats()
        insights = self.pattern_analyzer.get_optimization_insights()
        
        print(f"📈 System Statistics:")
        print(f"   Total Storage: {stats['total_storage_mb']:.2f} MB")
        print(f"   Active Partitions: {len(stats['partitions'])}")
        print(f"   Queries Analyzed: {insights['total_queries']}")
        
        print(f"\n🔍 Per-Partition Performance:")
        for partition, metrics in stats['partitions'].items():
            print(f"   {partition}:")
            print(f"     - Reads: {metrics['reads']}")
            print(f"     - Writes: {metrics['writes']}")
            print(f"     - Avg Query Time: {metrics['avg_query_time']:.3f}s")
            print(f"     - Storage: {metrics['storage_mb']:.2f} MB")

async def main():
    demo = StorageDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
