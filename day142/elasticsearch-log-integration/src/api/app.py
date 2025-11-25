from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import Optional
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

app = FastAPI(title="Elasticsearch Log Search API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global search engine reference (set by main)
search_engine = None
index_manager = None
log_indexer = None

class SearchRequest(BaseModel):
    query: Optional[str] = None
    level: Optional[str] = None
    service: Optional[str] = None
    time_range_minutes: int = 60
    size: int = 50

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Elasticsearch Log Search API", "status": "running"}

@app.post("/api/search")
async def search(request: SearchRequest):
    """Search logs"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    result = await search_engine.search_logs(
        query=request.query,
        level=request.level,
        service=request.service,
        time_range_minutes=request.time_range_minutes,
        size=request.size
    )
    
    return result

@app.get("/api/search")
async def search_get(
    q: Optional[str] = Query(None, description="Search query"),
    level: Optional[str] = Query(None, description="Log level filter"),
    service: Optional[str] = Query(None, description="Service filter"),
    time_range: int = Query(60, description="Time range in minutes"),
    size: int = Query(50, description="Number of results")
):
    """Search logs via GET"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    result = await search_engine.search_logs(
        query=q,
        level=level,
        service=service,
        time_range_minutes=time_range,
        size=size
    )
    
    return result

@app.get("/api/aggregations/levels")
async def aggregate_levels(time_range: int = Query(60, description="Time range in minutes")):
    """Get log counts by level"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    result = await search_engine.aggregate_by_level(time_range_minutes=time_range)
    return result

@app.get("/api/aggregations/timeline")
async def aggregate_timeline(
    interval: str = Query("1m", description="Time interval (1m, 5m, 1h)"),
    time_range: int = Query(60, description="Time range in minutes")
):
    """Get log volume over time"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    result = await search_engine.aggregate_over_time(
        interval=interval,
        time_range_minutes=time_range
    )
    return result

@app.get("/api/stats/indexing")
async def indexing_stats():
    """Get indexing statistics"""
    if not log_indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")
    
    stats = log_indexer.get_stats()
    return stats

@app.get("/api/stats/indices")
async def indices_stats():
    """Get index statistics"""
    if not index_manager:
        raise HTTPException(status_code=503, detail="Index manager not initialized")
    
    stats = await index_manager.get_index_stats()
    return {'indices': stats}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "search_engine": search_engine is not None,
            "index_manager": index_manager is not None,
            "log_indexer": log_indexer is not None
        }
    }

from .dashboard_routes import router as dashboard_router
app.include_router(dashboard_router)
