#!/bin/bash

# Test script for Day 62 implementation
set -e

echo "🧪 Running Distributed Log Processing System Tests - Day 62"
echo "======================================================="

# Backend tests
echo "🐍 Running backend tests..."
cd backend
python -m pytest tests/ -v --tb=short
echo "✅ Backend tests passed"

# Frontend tests (if any)
echo "⚛️  Checking frontend build..."
cd ../frontend
npm run build > /dev/null 2>&1
echo "✅ Frontend builds successfully"

cd ..

echo "🎉 All tests passed! System is ready for deployment."
