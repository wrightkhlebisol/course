from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os
from contextlib import contextmanager
from typing import Generator
import structlog

logger = structlog.get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:demo_password@localhost:5432/multitenant_logs")

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Get database session with proper cleanup"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_tenant_session(tenant_id: str):
    """Get database session with tenant context set"""
    db = SessionLocal()
    try:
        # Set tenant context for row-level security
        db.execute(text("SET app.current_tenant = :tenant_id"), {"tenant_id": tenant_id})
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Database session error", tenant_id=tenant_id, error=str(e))
        raise
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    from models.tenant import Base
    Base.metadata.create_all(bind=engine)

def setup_row_level_security():
    """Setup row-level security policies"""
    with engine.begin() as conn:
        # Enable RLS on log_entries
        conn.execute(text("""
            ALTER TABLE log_entries ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY tenant_isolation_policy ON log_entries
                FOR ALL TO current_user
                USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
        """))
        logger.info("Row-level security policies created")
