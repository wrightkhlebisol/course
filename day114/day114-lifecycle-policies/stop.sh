#!/bin/bash

echo "🛑 Stopping Data Lifecycle Policy Engine..."

# Find and kill backend processes
pkill -f "src.backend.api.main" || true

# Kill any remaining Python processes related to our app
pkill -f "uvicorn" || true
pkill -f "lifecycle" || true

echo "✅ All services stopped"
