FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY src/frontend/package*.json ./
RUN npm install
COPY src/frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY src/backend/ ./src/backend/
COPY config/ ./config/
COPY .env .

# Copy built frontend
COPY --from=frontend-build /app/frontend/build ./src/frontend/build

# Create storage directories
RUN mkdir -p storage/{hot,warm,cold,archive}

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "src.backend.api.main"]
