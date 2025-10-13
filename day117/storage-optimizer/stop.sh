#!/bin/bash

echo "🛑 Stopping Storage Optimization System"
echo "====================================="

# Kill backend processes
pkill -f "python src/main.py"

# Kill frontend processes  
pkill -f "npm start"

echo "✅ All services stopped"
