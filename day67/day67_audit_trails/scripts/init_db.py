#!/usr/bin/env python3

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from src.models.audit import Base
from config.settings import settings

def init_database():
    """Initialize the database with tables"""
    print("🗄️ Initializing database...")
    
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_database()
