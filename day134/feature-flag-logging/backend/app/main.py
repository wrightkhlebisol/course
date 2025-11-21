from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import json
from app.api.flags import router as flags_router
from app.core.database import create_tables
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

app = FastAPI(title="Feature Flag Logging System", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(flags_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database tables"""
    create_tables()

@app.get("/")
async def root():
    return {"message": "Feature Flag Logging System", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "feature-flag-logging"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
