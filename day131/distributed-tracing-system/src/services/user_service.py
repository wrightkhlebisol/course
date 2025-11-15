import time
import random
from fastapi import FastAPI, HTTPException
import structlog
from src.middleware.tracing import TracingMiddleware, TracedLogger
from config.config import service_config

app = FastAPI(title="User Service", version="1.0.0")
app.add_middleware(TracingMiddleware, service_name="user-service")

logger = TracedLogger("user-service")

# Mock user database
USERS_DB = {
    "user123": {"id": "user123", "name": "John Doe", "email": "john@example.com", "active": True},
    "user456": {"id": "user456", "name": "Jane Smith", "email": "jane@example.com", "active": True},
    "user789": {"id": "user789", "name": "Bob Wilson", "email": "bob@example.com", "active": False},
}

@app.get("/")
async def root():
    """User service health check"""
    logger.info("Health check requested")
    return {"service": "user-service", "status": "healthy"}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user by ID"""
    logger.info("User lookup", user_id=user_id)
    
    # Simulate database query delay
    await asyncio.sleep(random.uniform(0.01, 0.05))
    
    # Simulate occasional errors for testing
    if random.random() < 0.05:  # 5% error rate
        logger.error("Database connection error", user_id=user_id)
        raise HTTPException(status_code=500, detail="Database error")
    
    user = USERS_DB.get(user_id)
    if not user:
        logger.warning("User not found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user["active"]:
        logger.warning("User inactive", user_id=user_id)
        raise HTTPException(status_code=403, detail="User inactive")
    
    logger.info("User found", user_id=user_id, user_name=user["name"])
    return user

@app.post("/users")
async def create_user(user_data: dict):
    """Create new user"""
    logger.info("User creation requested", user_data=user_data)
    
    # Simulate validation and creation delay
    await asyncio.sleep(random.uniform(0.02, 0.08))
    
    user_id = f"user{random.randint(1000, 9999)}"
    new_user = {
        "id": user_id,
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "active": True
    }
    
    USERS_DB[user_id] = new_user
    logger.info("User created", user_id=user_id)
    
    return new_user

import asyncio

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.services.user_service:app",
        host="0.0.0.0",
        port=service_config.user_service_port,
        reload=False
    )
