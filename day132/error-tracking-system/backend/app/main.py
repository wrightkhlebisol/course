"""
Error Tracking System - Main FastAPI Application
Day 132: Error Tracking Features Implementation
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import uvicorn
from contextlib import asynccontextmanager

from app.api import errors, groups, alerts, analytics
from app.core.config import settings
from app.core.database import init_db
from app.services.websocket_manager import WebSocketManager
# Import models to ensure they're registered with Base metadata before init_db()
from app.models import error

# WebSocket connection manager
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup"""
    await init_db()
    yield

# Create FastAPI application
app = FastAPI(
    title="Error Tracking System",
    description="Intelligent error tracking with automatic grouping",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(errors.router, prefix="/api/v1/errors", tags=["errors"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "Error Tracking System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "error-tracking-api"}

@app.get("/health/db")
async def health_check_db():
    """Database health check endpoint"""
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.error import ErrorGroup
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ErrorGroup).limit(1))
            result.scalar_one_or_none()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
