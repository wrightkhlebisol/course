"""Database configuration and connection management"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import redis.asyncio as redis
from app.core.config import settings

# PostgreSQL async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Redis connection (optional, fail gracefully if not available)
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"⚠️ Redis connection failed (optional): {str(e)}")
    redis_client = None

async def get_db_session():
    """Get database session"""
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    except Exception as e:
        import traceback
        print(f"❌ Database session error: {str(e)}")
        traceback.print_exc()
        raise

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables initialized successfully")
    except Exception as e:
        import traceback
        print(f"❌ Error initializing database: {str(e)}")
        traceback.print_exc()
        # Don't raise - allow app to start even if DB init fails
        # The actual queries will handle the error
