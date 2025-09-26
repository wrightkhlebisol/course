FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend source and build
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build

# Copy backend source
COPY backend/ ./backend/

# Copy build artifacts to backend static directory
RUN cp -r frontend/build backend/static

# Create necessary directories
RUN mkdir -p data/{archives,cache,indexes} logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "backend/src/main.py"]
