#!/usr/bin/env python3

import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.adaptive_allocator import AdaptiveResourceAllocator
from monitoring.load_simulator import LoadSimulator

def run_demo():
    """Run comprehensive system demonstration"""
    print("🎬 Adaptive Resource Allocation System Demo")
    print("=" * 50)
    
    # Initialize components
    allocator = AdaptiveResourceAllocator()
    simulator = LoadSimulator()
    
    try:
        print("\n1️⃣ Starting system...")
        allocator.start()
        time.sleep(5)
        
        print("\n2️⃣ System baseline (30 seconds)...")
        for i in range(6):
            status = allocator.get_system_status()
            current = status['current_metrics']
            resources = status['resource_allocation']
            
            print(f"   [{i*5:2d}s] CPU: {current['cpu_percent']:5.1f}% | "
                  f"Memory: {current['memory_percent']:5.1f}% | "
                  f"Workers: {resources['current_workers']}")
            time.sleep(5)
            
        print("\n3️⃣ Simulating high CPU load...")
        simulator.simulate_cpu_load(target_percent=80, duration=60)
        
        print("   Monitoring scaling response (60 seconds)...")
        for i in range(12):
            status = allocator.get_system_status()
            current = status['current_metrics']
            resources = status['resource_allocation']
            
            print(f"   [{i*5:2d}s] CPU: {current['cpu_percent']:5.1f}% | "
                  f"Memory: {current['memory_percent']:5.1f}% | "
                  f"Workers: {resources['current_workers']} | "
                  f"Scaling: {'Yes' if resources['scaling_in_progress'] else 'No'}")
            time.sleep(5)
            
        print("\n4️⃣ Load spike complete, monitoring scale-down...")
        for i in range(12):
            status = allocator.get_system_status()
            current = status['current_metrics']
            resources = status['resource_allocation']
            
            print(f"   [{i*5:2d}s] CPU: {current['cpu_percent']:5.1f}% | "
                  f"Memory: {current['memory_percent']:5.1f}% | "
                  f"Workers: {resources['current_workers']} | "
                  f"Scaling: {'Yes' if resources['scaling_in_progress'] else 'No'}")
            time.sleep(5)
            
        print("\n5️⃣ Testing manual scaling...")
        print("   Manual scale up...")
        success = allocator.force_scaling_action('scale_up')
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        time.sleep(10)
        
        print("   Manual scale down...")
        success = allocator.force_scaling_action('scale_down')
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        time.sleep(10)
        
        print("\n6️⃣ Final system status...")
        status = allocator.get_system_status()
        current = status['current_metrics']
        resources = status['resource_allocation']
        summary = status['metrics_summary']
        
        print(f"   Current CPU: {current['cpu_percent']:.1f}%")
        print(f"   Current Memory: {current['memory_percent']:.1f}%")
        print(f"   Active Workers: {resources['current_workers']}")
        print(f"   Load Average: {current['load_average']:.2f}")
        
        if summary:
            print(f"   Avg CPU (15min): {summary['avg_cpu']:.1f}%")
            print(f"   Max CPU (15min): {summary['max_cpu']:.1f}%")
            
        print("\n✅ Demo completed successfully!")
        print("🌐 Web dashboard available at: http://localhost:8080")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        print("\n🧹 Cleaning up...")
        simulator.stop_simulation()
        allocator.stop()
        print("✅ Cleanup complete")

if __name__ == '__main__':
    run_demo()
