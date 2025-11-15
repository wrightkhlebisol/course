from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import structlog
from src.middleware.tracing import TracingMiddleware, TracedLogger
from src.tracing.context import TraceContextManager
from config.config import config, service_config

# Initialize structured logging
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
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

app = FastAPI(title="API Gateway", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tracing middleware
app.add_middleware(TracingMiddleware, service_name="api-gateway")

# Initialize traced logger
logger = TracedLogger("api-gateway")

@app.get("/")
async def root():
    """API Gateway health check"""
    logger.info("Health check requested")
    return {"service": "api-gateway", "status": "healthy"}

@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Proxy request to user service"""
    logger.info("User lookup requested", user_id=user_id)
    
    # Get trace context
    context = TraceContextManager.get_current_context()
    
    headers = {}
    if context:
        headers[config.trace_id_header] = context.trace_id
        headers[config.span_id_header] = context.span_id
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:{service_config.user_service_port}/users/{user_id}",
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                logger.info("User lookup successful", user_id=user_id)
                return response.json()
            else:
                logger.error("User lookup failed", user_id=user_id, status_code=response.status_code)
                raise HTTPException(status_code=response.status_code, detail="User service error")
                
    except httpx.TimeoutException:
        logger.error("User service timeout", user_id=user_id)
        raise HTTPException(status_code=504, detail="User service timeout")
    except Exception as e:
        logger.error("User service error", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/users/{user_id}/orders")
async def create_order(user_id: str, order_data: dict, request: Request):
    """Create order workflow spanning multiple services"""
    logger.info("Order creation requested", user_id=user_id)
    
    context = TraceContextManager.get_current_context()
    
    headers = {}
    if context:
        headers[config.trace_id_header] = context.trace_id
        headers[config.span_id_header] = context.span_id
    
    try:
        # Step 1: Validate user
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                f"http://localhost:{service_config.user_service_port}/users/{user_id}",
                headers=headers,
                timeout=5.0
            )
            
            if user_response.status_code != 200:
                logger.error("User validation failed", user_id=user_id)
                raise HTTPException(status_code=400, detail="Invalid user")
        
        # Step 2: Process order
        async with httpx.AsyncClient() as client:
            order_response = await client.post(
                f"http://localhost:{service_config.database_service_port}/orders",
                json={"user_id": user_id, **order_data},
                headers=headers,
                timeout=10.0
            )
            
            if order_response.status_code == 201:
                logger.info("Order created successfully", user_id=user_id, order_id=order_response.json().get("order_id"))
                return order_response.json()
            else:
                logger.error("Order creation failed", user_id=user_id, status_code=order_response.status_code)
                raise HTTPException(status_code=order_response.status_code, detail="Order creation failed")
                
    except httpx.TimeoutException:
        logger.error("Service timeout during order creation", user_id=user_id)
        raise HTTPException(status_code=504, detail="Service timeout")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Order creation error", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.services.api_gateway:app",
        host="0.0.0.0",
        port=service_config.api_gateway_port,
        reload=False
    )
