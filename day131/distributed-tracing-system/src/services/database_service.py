import time
import random
import uuid
from fastapi import FastAPI, HTTPException
import structlog
from src.middleware.tracing import TracingMiddleware, TracedLogger
from config.config import service_config

app = FastAPI(title="Database Service", version="1.0.0")
app.add_middleware(TracingMiddleware, service_name="database-service")

logger = TracedLogger("database-service")

# Mock orders database
ORDERS_DB = {}

@app.get("/")
async def root():
    """Database service health check"""
    logger.info("Health check requested")
    return {"service": "database-service", "status": "healthy"}

@app.post("/orders")
async def create_order(order_data: dict):
    """Create new order"""
    logger.info("Order creation requested", order_data=order_data)
    
    # Simulate database transaction delay
    await asyncio.sleep(random.uniform(0.05, 0.15))
    
    # Simulate occasional database errors
    if random.random() < 0.03:  # 3% error rate
        logger.error("Database transaction failed", order_data=order_data)
        raise HTTPException(status_code=500, detail="Database transaction failed")
    
    # Simulate occasional timeout for testing
    if random.random() < 0.02:  # 2% timeout rate
        logger.error("Database timeout", order_data=order_data)
        await asyncio.sleep(2)  # Simulate timeout
        raise HTTPException(status_code=504, detail="Database timeout")
    
    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "user_id": order_data.get("user_id"),
        "items": order_data.get("items", []),
        "total": order_data.get("total", 0.0),
        "status": "created",
        "created_at": time.time()
    }
    
    ORDERS_DB[order_id] = order
    logger.info("Order created", order_id=order_id, user_id=order_data.get("user_id"))
    
    return order

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order by ID"""
    logger.info("Order lookup", order_id=order_id)
    
    # Simulate database query delay
    await asyncio.sleep(random.uniform(0.01, 0.03))
    
    order = ORDERS_DB.get(order_id)
    if not order:
        logger.warning("Order not found", order_id=order_id)
        raise HTTPException(status_code=404, detail="Order not found")
    
    logger.info("Order found", order_id=order_id)
    return order

@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: str):
    """Get all orders for a user"""
    logger.info("User orders lookup", user_id=user_id)
    
    # Simulate database query delay
    await asyncio.sleep(random.uniform(0.02, 0.06))
    
    user_orders = [order for order in ORDERS_DB.values() if order["user_id"] == user_id]
    logger.info("User orders found", user_id=user_id, count=len(user_orders))
    
    return {"orders": user_orders}

import asyncio

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.services.database_service:app",
        host="0.0.0.0",
        port=service_config.database_service_port,
        reload=False
    )
