#!/bin/bash

echo "🛑 Stopping Tenant Lifecycle Management System"
echo "=============================================="

# Kill servers using saved PIDs
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null || true
    rm -f .backend.pid
    echo "✅ Backend server stopped"
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f .frontend.pid
    echo "✅ Frontend server stopped"
fi

# Kill any remaining processes
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

echo "✅ All servers stopped"
