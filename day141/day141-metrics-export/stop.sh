#!/bin/bash

echo "🛑 Stopping Metrics Export System"
pkill -f "python -m src.main" || true
echo "✅ System stopped"
