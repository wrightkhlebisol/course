from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.tenant_api import router as tenant_router
from api.logs_api import router as logs_router
from database.connection import create_tables, setup_row_level_security
from contextlib import asynccontextmanager
import structlog
import uvicorn
import os

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Initializing database...")
        create_tables()
        
        # Note: Row-level security setup would need superuser privileges
        # In production, this would be done during deployment
        # setup_row_level_security()
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(
    title="Multi-Tenant Log Processing Platform",
    description="A scalable multi-tenant log processing platform with complete data isolation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tenant_router)
app.include_router(logs_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multitenant-log-platform"}

# Database initialization is now handled in the lifespan function

# Serve static files for frontend
if os.path.exists("../frontend/build"):
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse("../frontend/build/index.html")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
