import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.indexing.inverted_index import InvertedIndex
from src.indexing.tokenizer import LogTokenizer
from src.search.query_engine import QueryEngine
from src.api.search_api import SearchAPI
from src.storage.index_storage import IndexStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

inverted_index = None
query_engine = None
search_api = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global inverted_index, query_engine, search_api
    
    print("🚀 Starting Inverted Index Log Search System...")
    
    # Create storage directory if it doesn't exist
    os.makedirs("storage", exist_ok=True)
    
    tokenizer = LogTokenizer()
    storage = IndexStorage("storage/index.json")
    inverted_index = InvertedIndex(tokenizer, storage)
    query_engine = QueryEngine(inverted_index)
    search_api = SearchAPI(query_engine, inverted_index)
    
    await inverted_index.load_from_storage()
    await generate_sample_logs()
    print("✅ System initialized successfully")
    yield
    
    await inverted_index.save_to_storage()
    print("💾 Index saved to storage")

app = FastAPI(title="Log Search System", description="Inverted Index based log search engine", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from src.api.search_api import router as search_router
app.include_router(search_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Log Search System is running"}

@app.get("/health")
async def health_check():
    if inverted_index:
        stats = await inverted_index.get_stats()
        return {"status": "healthy", "index_stats": stats, "version": "1.0.0"}
    else:
        return {"status": "initializing", "version": "1.0.0"}

async def generate_sample_logs():
    sample_logs = [
        {"id": "log_001", "timestamp": "2025-05-15T10:00:00Z", "level": "ERROR", "service": "auth-service", "message": "Authentication failed for user john.doe@example.com"},
        {"id": "log_002", "timestamp": "2025-05-15T10:01:00Z", "level": "INFO", "service": "api-gateway", "message": "Request processed successfully for /api/users"},
        {"id": "log_003", "timestamp": "2025-05-15T10:02:00Z", "level": "WARNING", "service": "database", "message": "Slow query detected: SELECT * FROM users WHERE active = true"},
        {"id": "log_004", "timestamp": "2025-05-15T10:03:00Z", "level": "ERROR", "service": "payment-service", "message": "Payment processing failed: insufficient funds"},
        {"id": "log_005", "timestamp": "2025-05-15T10:04:00Z", "level": "INFO", "service": "auth-service", "message": "User session created for admin@example.com"},
        {"id": "log_006", "timestamp": "2025-05-15T10:05:00Z", "level": "ERROR", "service": "api-gateway", "message": "Rate limit exceeded for client 192.168.1.100"},
        {"id": "log_007", "timestamp": "2025-05-15T10:06:00Z", "level": "INFO", "service": "database", "message": "Database backup completed successfully"},
        {"id": "log_008", "timestamp": "2025-05-15T10:07:00Z", "level": "WARNING", "service": "payment-service", "message": "High transaction volume detected"},
        {"id": "log_009", "timestamp": "2025-05-15T10:08:00Z", "level": "ERROR", "service": "notification-service", "message": "Failed to send email notification to user@example.com"},
        {"id": "log_010", "timestamp": "2025-05-15T10:09:00Z", "level": "INFO", "service": "auth-service", "message": "Password reset requested for user@example.com"}
    ]
    
    for log_entry in sample_logs:
        await inverted_index.add_document(log_entry)
    logger.info(f"Generated {len(sample_logs)} sample log entries")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
