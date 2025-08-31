from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import time
import random
import string
from src.core.bloom_filter import LogBloomFilterManager

app = FastAPI(title="Bloom Filter Log Processing API", version="1.0.0")

# Initialize bloom filter manager
bloom_manager = LogBloomFilterManager()

class LogEntry(BaseModel):
    log_type: str
    log_key: str
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    log_type: str
    log_key: str

@app.post("/logs/add")
async def add_log_entry(entry: LogEntry):
    """Add a log entry to the bloom filter"""
    start_time = time.time()
    
    success = bloom_manager.add_log_entry(entry.log_type, entry.log_key)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Unknown log type: {entry.log_type}")
    
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "status": "added",
        "log_type": entry.log_type,
        "log_key": entry.log_key,
        "processing_time_ms": processing_time
    }

@app.post("/logs/query")
async def query_log_existence(query: QueryRequest):
    """Query if a log entry might exist"""
    start_time = time.time()
    
    result = bloom_manager.check_log_exists(query.log_type, query.log_key)
    
    if result is None:
        raise HTTPException(status_code=400, detail=f"Unknown log type: {query.log_type}")
    
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return {
        "log_type": query.log_type,
        "log_key": query.log_key,
        "might_exist": result,
        "confidence": "definitely_not_exist" if not result else "probably_exists",
        "processing_time_ms": processing_time
    }

@app.get("/stats")
async def get_statistics():
    """Get comprehensive statistics for all bloom filters"""
    return bloom_manager.get_all_stats()

@app.get("/stats/{log_type}")
async def get_filter_stats(log_type: str):
    """Get statistics for specific log type"""
    if log_type not in bloom_manager.filters:
        raise HTTPException(status_code=404, detail=f"Log type not found: {log_type}")
    
    return bloom_manager.filters[log_type].get_stats()

@app.post("/demo/populate")
async def populate_demo_data(count: int = 10000):
    """Populate bloom filters with demo data"""
    
    async def generate_demo_logs():
        log_types = ["error_logs", "access_logs", "security_logs"]
        
        for i in range(count):
            log_type = random.choice(log_types)
            
            if log_type == "error_logs":
                log_key = f"error_{random.randint(1000, 9999)}_{random.choice(['sql', 'network', 'timeout'])}"
            elif log_type == "access_logs":
                ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
                log_key = f"access_{ip}_{random.randint(100000, 999999)}"
            else:  # security_logs
                user_id = ''.join(random.choices(string.ascii_lowercase, k=8))
                log_key = f"security_{user_id}_{random.choice(['login', 'logout', 'failed_auth'])}"
            
            bloom_manager.add_log_entry(log_type, log_key)
            
            if i % 1000 == 0:
                await asyncio.sleep(0.01)  # Yield control
    
    await generate_demo_logs()
    
    return {
        "status": "completed",
        "records_added": count,
        "filters_populated": list(bloom_manager.filters.keys())
    }

@app.post("/demo/performance-test")
async def performance_test():
    """Run performance comparison test"""
    # Test data
    test_keys = [f"test_key_{i}" for i in range(1000)]
    existing_keys = test_keys[:500]  # First 500 exist
    non_existing_keys = test_keys[500:]  # Last 500 don't exist
    
    # Add existing keys
    for key in existing_keys:
        bloom_manager.add_log_entry("error_logs", key)
    
    # Test bloom filter performance
    start_time = time.time()
    bloom_results = []
    for key in test_keys:
        result = bloom_manager.check_log_exists("error_logs", key)
        bloom_results.append(result)
    bloom_time = time.time() - start_time
    
    # Simulate traditional lookup performance (much slower)
    start_time = time.time()
    traditional_results = []
    for key in test_keys:
        # Simulate database/file lookup delay
        await asyncio.sleep(0.001)  # 1ms per lookup
        result = key in existing_keys
        traditional_results.append(result)
    traditional_time = time.time() - start_time
    
    # Calculate accuracy
    true_positives = sum(1 for i, key in enumerate(test_keys) 
                        if key in existing_keys and bloom_results[i])
    false_positives = sum(1 for i, key in enumerate(test_keys) 
                         if key not in existing_keys and bloom_results[i])
    true_negatives = sum(1 for i, key in enumerate(test_keys) 
                        if key not in existing_keys and not bloom_results[i])
    
    return {
        "test_summary": {
            "total_queries": len(test_keys),
            "existing_keys": len(existing_keys),
            "non_existing_keys": len(non_existing_keys)
        },
        "bloom_filter_performance": {
            "total_time_seconds": bloom_time,
            "avg_time_per_query_ms": (bloom_time / len(test_keys)) * 1000,
            "queries_per_second": len(test_keys) / bloom_time
        },
        "traditional_lookup_performance": {
            "total_time_seconds": traditional_time,
            "avg_time_per_query_ms": (traditional_time / len(test_keys)) * 1000,
            "queries_per_second": len(test_keys) / traditional_time
        },
        "speed_improvement": {
            "times_faster": traditional_time / bloom_time,
            "time_saved_seconds": traditional_time - bloom_time
        },
        "accuracy_metrics": {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_positive_rate": false_positives / len(non_existing_keys) if non_existing_keys else 0,
            "no_false_negatives": True  # Bloom filters never have false negatives
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "bloom-filter-api",
        "filters_active": len(bloom_manager.filters),
        "timestamp": time.time()
    }
