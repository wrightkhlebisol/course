#!/usr/bin/env python3

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime
import asyncio
from pathlib import Path
import sys
import os

# Add src to path
sys.path.append(str(Path(__file__).parent))

from api.routes import retention_router, compliance_router, storage_router, logs_router
from utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Data Retention System",
    description="Automated data retention policies with compliance management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files if build exists
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Include routers
app.include_router(retention_router, prefix="/api/retention", tags=["retention"])
app.include_router(compliance_router, prefix="/api/compliance", tags=["compliance"])
app.include_router(storage_router, prefix="/api/storage", tags=["storage"])
app.include_router(logs_router, prefix="/api/logs", tags=["logs"])

@app.get("/")
async def root():
    """Root endpoint - serve frontend or API info"""
    if os.path.exists("frontend/build/index.html"):
        return FileResponse("frontend/build/index.html")
    else:
        return {
            "message": "Data Retention System API",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "running"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "database": "connected",
            "storage": "available"
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "total_logs_processed": 0,
            "retention_policies": 0,
            "storage_usage": {
                "hot": "0 MB",
                "warm": "0 MB", 
                "cold": "0 MB"
            },
            "compliance_score": 100.0
        }
    }



@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend for client-side routing"""
    # Skip API routes and known endpoints
    if (full_path.startswith("api/") or 
        full_path in ["health", "metrics", "docs", "redoc", "openapi.json", "static"]):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    if os.path.exists("frontend/build/index.html"):
        return FileResponse("frontend/build/index.html")
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    logger.info("Starting Data Retention System...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 