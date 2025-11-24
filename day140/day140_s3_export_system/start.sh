#!/bin/bash
set -e

echo "🚀 Starting S3 Export System"

# Set AWS credentials for MinIO (local development)
# For AWS S3, set these to your actual AWS credentials
export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-minioadmin}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-minioadmin}

echo "📋 Using credentials:"
echo "   AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}"
echo "   AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:0:4}****"

# Activate virtual environment
source venv/bin/activate

# Start application
echo "🌐 Starting API server on http://localhost:8000"
python src/main.py
