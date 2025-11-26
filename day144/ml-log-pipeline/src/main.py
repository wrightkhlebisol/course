"""Main application entry point"""
import sys
import subprocess
from pathlib import Path

def run_training():
    """Run model training"""
    from src.training.trainer import ModelTrainer
    
    trainer = ModelTrainer()
    trainer.train_all_models("data/processed/training_logs.json")

def run_api():
    """Start inference API"""
    subprocess.run([
        "uvicorn", "src.api.server:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])

def run_dashboard():
    """Serve dashboard"""
    import http.server
    import socketserver
    import os
    
    # Generate dashboard HTML first
    from src.dashboard import app
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Change to static directory for serving
    static_dir = project_root / "src" / "dashboard" / "static"
    if not static_dir.exists():
        raise FileNotFoundError(f"Dashboard static directory not found: {static_dir}")
    
    os.chdir(static_dir)
    
    PORT = 3000
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Dashboard running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.main [train|api|dashboard]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "train":
        run_training()
    elif command == "api":
        run_api()
    elif command == "dashboard":
        run_dashboard()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
