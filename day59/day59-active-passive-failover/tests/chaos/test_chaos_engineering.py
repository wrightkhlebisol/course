import pytest
import asyncio
import random
import time
from src.backend.nodes.log_processor import LogProcessorNode
from src.shared.models import NodeState, NodeRole

@pytest.mark.asyncio
class TestChaosEngineering:
    
    @pytest.fixture
    async def chaos_cluster(self):
        """Create a larger cluster for chaos testing"""
        nodes = []
        
        # Create primary node
        primary = LogProcessorNode("primary", 8001, is_primary=True)
        nodes.append(primary)
        
        # Create standby nodes
        for i in range(4):
            standby = LogProcessorNode(f"standby_{i}", 8002 + i, is_primary=False)
            nodes.append(standby)
        
        # Start all nodes
        for node in nodes:
            await node.start()
        
        yield nodes
        
        # Cleanup
        for node in nodes:
            if node.running:
                await node.stop()
    
    async def test_random_node_failures(self, chaos_cluster):
        """Test random node failures"""
        print("🔥 Starting chaos test: Random node failures")
        
        # Run chaos test for 60 seconds
        test_duration = 60
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            # Randomly select a node to fail
            running_nodes = [node for node in chaos_cluster if node.running]
            
            if len(running_nodes) > 1:  # Keep at least one node running
                victim = random.choice(running_nodes)
                print(f"💥 Killing node: {victim.node_id}")
                await victim.stop()
                
                # Wait for failover
                await asyncio.sleep(5)
                
                # Verify system still has a primary
                primary_count = sum(1 for node in chaos_cluster 
                                  if node.running and node.role == NodeRole.PRIMARY)
                assert primary_count <= 1, "Multiple primaries detected!"
                
                # Restart the failed node
                print(f"🔄 Restarting node: {victim.node_id}")
                await victim.start()
                
                # Wait for stabilization
                await asyncio.sleep(10)
        
        print("✅ Chaos test completed successfully")
    
    async def test_network_partitions(self, chaos_cluster):
        """Test network partition scenarios"""
        print("🌐 Starting chaos test: Network partitions")
        
        # Simulate network partition by stopping heartbeats
        primary = chaos_cluster[0]
        
        # Stop primary heartbeat (simulate network partition)
        await primary.heartbeat_manager.stop()
        
        # Wait for partition detection
        await asyncio.sleep(15)
        
        # Verify standby nodes elected new primary
        standby_nodes = chaos_cluster[1:]
        primary_count = sum(1 for node in standby_nodes 
                          if node.role == NodeRole.PRIMARY)
        
        assert primary_count == 1, "No new primary elected during partition"
        
        # Restore network (restart heartbeat)
        await primary.heartbeat_manager.start()
        
        # Wait for network restoration
        await asyncio.sleep(10)
        
        # Verify split-brain didn't occur
        total_primaries = sum(1 for node in chaos_cluster 
                            if node.running and node.role == NodeRole.PRIMARY)
        assert total_primaries == 1, "Split-brain scenario detected!"
        
        print("✅ Network partition test completed successfully")
    
    async def test_cascading_failures(self, chaos_cluster):
        """Test cascading failure scenarios"""
        print("⚡ Starting chaos test: Cascading failures")
        
        # Simulate cascading failures
        for i in range(3):
            # Find current primary
            primary_node = None
            for node in chaos_cluster:
                if node.running and node.role == NodeRole.PRIMARY:
                    primary_node = node
                    break
            
            if primary_node:
                print(f"💥 Cascade failure #{i+1}: Killing primary {primary_node.node_id}")
                await primary_node.stop()
                
                # Wait for failover
                await asyncio.sleep(8)
                
                # Verify system recovered
                remaining_nodes = [node for node in chaos_cluster if node.running]
                primary_count = sum(1 for node in remaining_nodes 
                                  if node.role == NodeRole.PRIMARY)
                
                assert primary_count == 1, f"No primary after cascade failure #{i+1}"
                
                # Wait before next failure
                await asyncio.sleep(5)
        
        print("✅ Cascading failure test completed successfully")
    
    async def test_load_during_failures(self, chaos_cluster):
        """Test system behavior under load during failures"""
        print("📊 Starting chaos test: Load during failures")
        
        # Start continuous load
        load_task = asyncio.create_task(self.generate_load(chaos_cluster))
        
        # Start failure injection
        failure_task = asyncio.create_task(self.inject_failures(chaos_cluster))
        
        # Run for 60 seconds
        await asyncio.sleep(60)
        
        # Stop tasks
        load_task.cancel()
        failure_task.cancel()
        
        # Wait for cleanup
        await asyncio.gather(load_task, failure_task, return_exceptions=True)
        
        print("✅ Load during failures test completed successfully")
    
    async def generate_load(self, nodes):
        """Generate continuous load on the system"""
        while True:
            # Find primary node
            primary = None
            for node in nodes:
                if node.running and node.role == NodeRole.PRIMARY:
                    primary = node
                    break
            
            if primary:
                # Generate log entries
                for i in range(10):
                    log_entry = type('LogEntry', (), {
                        'timestamp': time.time(),
                        'level': random.choice(['INFO', 'WARN', 'ERROR']),
                        'message': f'Load test message {i}',
                        'source': 'chaos_test',
                        'metadata': {}
                    })()
                    primary.log_buffer.append(log_entry)
            
            await asyncio.sleep(1)
    
    async def inject_failures(self, nodes):
        """Inject random failures"""
        while True:
            # Wait random time between failures
            await asyncio.sleep(random.uniform(5, 15))
            
            # Randomly fail a node
            running_nodes = [node for node in nodes if node.running]
            if len(running_nodes) > 1:
                victim = random.choice(running_nodes)
                print(f"🎯 Injecting failure: {victim.node_id}")
                await victim.stop()
                
                # Wait and restart
                await asyncio.sleep(random.uniform(3, 10))
                await victim.start()
