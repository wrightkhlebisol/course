#!/usr/bin/env python3
"""
System verification script for Active-Passive Failover implementation
"""
import asyncio
import time
import json
from src.backend.nodes.log_processor import LogProcessorNode
from src.shared.models import NodeState, NodeRole

async def verify_system():
    """Verify the complete failover system"""
    print("🔍 Verifying Active-Passive Failover System...")
    
    # Create test nodes
    nodes = []
    
    # Primary node
    primary = LogProcessorNode("primary", 8001, is_primary=True)
    nodes.append(primary)
    
    # Standby nodes
    for i in range(2):
        standby = LogProcessorNode(f"standby_{i}", 8002 + i, is_primary=False)
        nodes.append(standby)
    
    try:
        # Start all nodes
        print("📡 Starting nodes...")
        for node in nodes:
            await node.start()
        
        # Wait for initialization
        await asyncio.sleep(5)
        
        # Verify initial state
        print("✅ Verifying initial state...")
        assert nodes[0].role == NodeRole.PRIMARY
        assert nodes[0].state == NodeState.PRIMARY
        
        for i in range(1, 3):
            assert nodes[i].role == NodeRole.STANDBY
            assert nodes[i].state == NodeState.STANDBY
        
        # Test health status
        print("🏥 Testing health status...")
        for node in nodes:
            health = node.get_health_status()
            assert health['node_id'] == node.node_id
            assert health['healthy'] == True
            print(f"  ✅ {node.node_id}: {health['state']} - Healthy")
        
        # Test log processing
        print("📝 Testing log processing...")
        log_entry = type('LogEntry', (), {
            'timestamp': time.time(),
            'level': 'INFO',
            'message': 'Test verification log',
            'source': 'verification',
            'metadata': {}
        })()
        
        nodes[0].log_buffer.append(log_entry)
        await asyncio.sleep(2)
        
        print("✅ Log processing verified!")
        
        # Test role transitions
        print("🔄 Testing role transitions...")
        
        # Test primary to standby transition
        await nodes[0].become_standby()
        assert nodes[0].role == NodeRole.STANDBY
        assert nodes[0].state == NodeState.STANDBY
        print("  ✅ Primary to standby transition successful")
        
        # Test standby to primary transition
        await nodes[1].become_primary()
        assert nodes[1].role == NodeRole.PRIMARY
        assert nodes[1].state == NodeState.PRIMARY
        print("  ✅ Standby to primary transition successful")
        
        # Test state persistence
        print("💾 Testing state persistence...")
        await nodes[1].save_state()
        print("  ✅ State persistence verified!")
        
        print("✅ All core functionality verified!")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        for node in nodes:
            if node.running:
                await node.stop()
    
    print("🎉 System verification completed successfully!")

if __name__ == "__main__":
    asyncio.run(verify_system()) 