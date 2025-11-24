"""Main application entry point."""
import uvicorn
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.app import app

if __name__ == "__main__":
    # Serve static files
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory="src/web/static", html=True), name="static")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
