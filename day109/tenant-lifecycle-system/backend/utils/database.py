from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.tenant import Base, TenantModel
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tenants.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
