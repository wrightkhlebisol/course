import psutil
import time
import threading
import random
import multiprocessing as mp
from typing import Optional

class LoadSimulator:
    def __init__(self):
        self.cpu_load_process: Optional[mp.Process] = None
        self.memory_hog_process: Optional[mp.Process] = None
        self.running = False
        
    def simulate_cpu_load(self, target_percent: int = 70, duration: int = 60):
        """Simulate CPU load for testing"""
        print(f"🔥 Simulating {target_percent}% CPU load for {duration} seconds")
        
        def cpu_worker():
            end_time = time.time() + duration
            while time.time() < end_time:
                # Busy work to consume CPU
                for _ in range(10000):
                    _ = sum(range(100))
                    
                # Check current CPU and adjust
                current_cpu = psutil.cpu_percent(interval=0.1)
                if current_cpu < target_percent:
                    # Work harder
                    for _ in range(50000):
                        _ = sum(range(100))
                else:
                    # Rest a bit
                    time.sleep(0.01)
                    
        self.cpu_load_process = mp.Process(target=cpu_worker)
        self.cpu_load_process.start()
        
    def simulate_memory_load(self, target_mb: int = 500, duration: int = 60):
        """Simulate memory load for testing"""
        print(f"🧠 Simulating {target_mb}MB memory usage for {duration} seconds")
        
        def memory_worker():
            # Allocate memory
            data = []
            chunk_size = 1024 * 1024  # 1MB chunks
            
            for _ in range(target_mb):
                data.append(bytearray(chunk_size))
                time.sleep(0.1)  # Gradual allocation
                
            # Hold memory for duration
            time.sleep(duration)
            
            # Cleanup
            del data
            
        self.memory_load_process = mp.Process(target=memory_worker)
        self.memory_load_process.start()
        
    def simulate_variable_load(self, duration: int = 300):
        """Simulate variable load patterns"""
        print(f"📊 Simulating variable load for {duration} seconds")
        
        def variable_load_worker():
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Random load spikes
                if random.random() < 0.3:  # 30% chance of spike
                    spike_duration = random.randint(10, 30)
                    target_cpu = random.randint(60, 90)
                    
                    print(f"⚡ Load spike: {target_cpu}% CPU for {spike_duration}s")
                    
                    spike_end = time.time() + spike_duration
                    while time.time() < spike_end:
                        for _ in range(100000):
                            _ = sum(range(50))
                        time.sleep(0.01)
                else:
                    # Normal load
                    time.sleep(random.uniform(5, 15))
                    
        load_thread = threading.Thread(target=variable_load_worker, daemon=True)
        load_thread.start()
        
    def stop_simulation(self):
        """Stop all load simulations"""
        print("⏹️ Stopping load simulation")
        
        if self.cpu_load_process and self.cpu_load_process.is_alive():
            self.cpu_load_process.terminate()
            self.cpu_load_process.join()
            
        if self.memory_load_process and self.memory_load_process.is_alive():
            self.memory_load_process.terminate()
            self.memory_load_process.join()
            
        print("✅ Load simulation stopped")

def main():
    """Demo load simulation"""
    simulator = LoadSimulator()
    
    try:
        print("🎬 Starting load simulation demo")
        print("This will generate various load patterns for 2 minutes")
        
        # Start variable load
        simulator.simulate_variable_load(120)
        
        # Wait for completion
        time.sleep(120)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulation")
    finally:
        simulator.stop_simulation()

if __name__ == '__main__':
    main()
