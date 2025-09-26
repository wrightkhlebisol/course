#!/bin/bash
echo "🛑 Stopping Archive Restoration System"

# Kill any Python processes running the main application
pkill -f "python -m src.main" || true
pkill -f "uvicorn" || true

echo "✅ System stopped"
