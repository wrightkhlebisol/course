"""
Distributed Log Processing System - Day 62: Backpressure Mechanisms
Main application entry point with backpressure control
"""
import asyncio
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import structlog

from core.backpressure_manager import BackpressureManager
from core.log_processor import LogProcessor
from core.circuit_breaker import CircuitBreaker
from api.routes import router
from utils.metrics import MetricsCollector

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global components
backpressure_manager = None
log_processor = None
circuit_breaker = None
metrics_collector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global backpressure_manager, log_processor, circuit_breaker, metrics_collector
    
    # Startup
    print("🚀 Starting Distributed Log Processing System with Backpressure...")
    startup_start = time.time()
    
    # Initialize components quickly with minimal blocking
    print("   📊 Initializing metrics collector...")
    metrics_collector = MetricsCollector()
    
    print("   🔧 Initializing circuit breaker...")
    circuit_breaker = CircuitBreaker()
    
    print("   🔄 Initializing backpressure manager...")
    backpressure_manager = BackpressureManager(metrics_collector)
    
    print("   ⚙️  Initializing log processor...")
    log_processor = LogProcessor(backpressure_manager, circuit_breaker, metrics_collector)
    
    # Start background tasks concurrently
    print("   🚀 Starting background services...")
    await asyncio.gather(
        backpressure_manager.start(),
        log_processor.start()
    )
    
    app.state.backpressure_manager = backpressure_manager
    app.state.log_processor = log_processor
    app.state.circuit_breaker = circuit_breaker
    app.state.metrics_collector = metrics_collector
    
    startup_time = time.time() - startup_start
    print(f"   ✅ System startup completed in {startup_time:.3f}s")
    logger.info("System components initialized successfully", startup_time=startup_time)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down system components...")
    await log_processor.stop()
    await backpressure_manager.stop()
    logger.info("System shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Distributed Log Processing System - Day 62",
    description="Backpressure Mechanisms for Graceful Load Management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backpressure middleware
@app.middleware("http")
async def backpressure_middleware(request: Request, call_next):
    """Apply backpressure to incoming requests"""
    if hasattr(app.state, 'backpressure_manager'):
        allowed = await app.state.backpressure_manager.should_accept_request()
        if not allowed:
            # Create 429 response with CORS headers
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "System under high load",
                    "message": "Please retry after a moment",
                    "retry_after": 5
                }
            )
            # Add CORS headers manually for 429 responses
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
    
    response = await call_next(request)
    return response

# Include API routes FIRST - these take precedence
app.include_router(router, prefix="/api/v1")

# Add a root redirect to help with routing
@app.get("/api/v1/")
async def api_root():
    """API root endpoint"""
    return {"message": "Distributed Log Processing System API - Day 62", "version": "1.0.0"}

# Mount static files for assets (CSS, JS, etc.)
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "build", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted from: {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}. Frontend may not be built.")

# Serve React app for all other routes (SPA catch-all)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve React SPA for all non-API routes"""
    from fastapi.responses import FileResponse
    
    # Don't serve SPA for API routes (should not reach here)
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Serve index.html for all other routes
    index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "build", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    # Use environment variable to control reload for faster startup in production
    import os
    reload_enabled = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        log_level="info",
        # Optimize for faster startup
        access_log=False,  # Disable access log for better performance
        server_header=False,  # Disable server header
        date_header=False,  # Disable date header
    )
