# Multi-stage Dockerfile for Slack Integration
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY package.json ./
RUN npm install --silent
COPY src/frontend/ ./src/
COPY public/ ./public/
RUN npm run build

FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/backend/ ./src/backend/
COPY --from=frontend-builder /app/frontend/build ./build

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 8000

CMD ["python", "-m", "src.backend.main"]
