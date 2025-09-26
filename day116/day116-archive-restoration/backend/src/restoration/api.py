from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from typing import Optional
import logging

from restoration.models import QueryRequest, QueryResponse
from query.processor import QueryProcessor
from archive.locator import ArchiveLocator
from restoration.decompressor import StreamingDecompressor
from cache.manager import SmartCache
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
archive_locator = ArchiveLocator(settings.archive_base_path, settings.index_path)
decompressor = StreamingDecompressor(settings.chunk_size)
cache = SmartCache(settings.cache_path, settings.cache_size_mb)
query_processor = QueryProcessor(archive_locator, decompressor, cache)

# Create FastAPI app
app = FastAPI(title="Archive Restoration API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend (if build exists)
import os
if os.path.exists("static/static"):
    app.mount("/static", StaticFiles(directory="static/static"), name="static")
elif os.path.exists("../static/static"):
    app.mount("/static", StaticFiles(directory="../static/static"), name="static")

@app.get("/")
async def root():
    # Try to serve the frontend if it exists, otherwise return API info
    static_paths = ["static/index.html", "../static/index.html"]
    for path in static_paths:
        if os.path.exists(path):
            return FileResponse(path)
    return {"message": "Archive Restoration API", "version": "1.0.0"}

@app.post("/api/query", response_model=QueryResponse)
async def execute_query(query: QueryRequest):
    """Execute archive restoration query"""
    try:
        # Normalize datetime objects to be timezone-naive
        if query.start_time.tzinfo is not None:
            query.start_time = query.start_time.replace(tzinfo=None)
        if query.end_time.tzinfo is not None:
            query.end_time = query.end_time.replace(tzinfo=None)
        
        # Validate date range
        if query.end_time <= query.start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        max_days = timedelta(days=settings.max_query_days)
        if query.end_time - query.start_time > max_days:
            raise HTTPException(
                status_code=400, 
                detail=f"Query range too large. Maximum {settings.max_query_days} days allowed"
            )
        
        result = await query_processor.execute_query(query)
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of streaming query job"""
    job = await query_processor.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job

@app.get("/api/archives")
async def list_archives():
    """List available archives"""
    try:
        await archive_locator._ensure_index_loaded()
        
        archives = []
        for file_path, metadata in archive_locator.metadata_cache.items():
            archives.append({
                "file_path": file_path,
                "start_time": metadata.start_time.isoformat(),
                "end_time": metadata.end_time.isoformat(),
                "compression": metadata.compression,
                "record_count": metadata.record_count,
                "size_mb": metadata.compressed_size / (1024 * 1024)
            })
        
        return {"archives": archives, "total": len(archives)}
        
    except Exception as e:
        logger.error(f"Failed to list archives: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    try:
        cache_stats = await cache.get_stats()
        
        return {
            "cache": cache_stats,
            "archives": {
                "total": len(archive_locator.metadata_cache),
                "last_scan": archive_locator.last_scan.isoformat() if archive_locator.last_scan else None
            },
            "active_jobs": len(query_processor.active_jobs)
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/refresh-index")
async def refresh_archive_index():
    """Manually refresh archive index"""
    try:
        await archive_locator._rebuild_index()
        return {"message": "Archive index refreshed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to refresh index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/cache")
async def clear_cache():
    """Clear all cached data"""
    try:
        await cache.clear()
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sample data endpoints for demo
@app.post("/api/demo/create-sample-archives")
async def create_sample_archives():
    """Create sample archive files for demonstration"""
    import os
    import json
    import gzip
    from pathlib import Path
    
    archive_path = Path(settings.archive_base_path)
    archive_path.mkdir(parents=True, exist_ok=True)
    
    # Create sample archives
    sample_data = []
    for i in range(5):
        start_time = datetime.now() - timedelta(days=i+1)
        end_time = start_time + timedelta(hours=23, minutes=59)
        
        # Create sample log entries
        logs = []
        for j in range(100):
            log_entry = {
                "timestamp": (start_time + timedelta(minutes=j*10)).isoformat(),
                "level": "INFO" if j % 3 != 0 else "ERROR",
                "service": f"service-{j % 3}",
                "message": f"Sample log message {j}",
                "request_id": f"req-{i}-{j}"
            }
            logs.append(json.dumps(log_entry))
        
        # Write compressed archive
        archive_filename = f"logs_{start_time.strftime('%Y-%m-%dT%H-%M-%S')}_{end_time.strftime('%Y-%m-%dT%H-%M-%S')}.archive"
        archive_file = archive_path / archive_filename
        
        with gzip.open(archive_file, 'wt') as f:
            f.write('\n'.join(logs))
        
        sample_data.append({
            "file": archive_filename,
            "records": len(logs),
            "time_range": f"{start_time.isoformat()} to {end_time.isoformat()}"
        })
    
    # Refresh index to pick up new files
    await archive_locator._rebuild_index()
    
    return {"message": "Sample archives created", "files": sample_data}
