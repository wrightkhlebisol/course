#!/bin/bash

echo "🛑 Stopping Container Log Collector"

# Kill any running Python processes
pkill -f "python -m src.main" || true

echo "✅ Stopped"
