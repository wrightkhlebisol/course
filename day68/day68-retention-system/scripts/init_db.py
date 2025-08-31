#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

def init_database():
    """Initialize database with tables"""
    print("🗄️ Initializing database...")
    
    # For now, we'll use a simple file-based storage
    # In a real implementation, this would create SQLAlchemy tables
    
    # Create storage directories
    storage_dirs = [
        "/tmp/logs/hot",
        "/tmp/logs/warm", 
        "/tmp/logs/cold"
    ]
    
    for dir_path in storage_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created directory: {dir_path}")
    
    print("✅ Database initialization completed!")
    print("📁 Storage directories created:")
    for dir_path in storage_dirs:
        print(f"  • {dir_path}")

if __name__ == "__main__":
    init_database() 