from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.feature_flag import Base as FlagBase
from app.models.flag_log import Base as LogBase
from app.models.user import Base as UserBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/featureflags")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    FlagBase.metadata.create_all(bind=engine)
    LogBase.metadata.create_all(bind=engine)
    UserBase.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
