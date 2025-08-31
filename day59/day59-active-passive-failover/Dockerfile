FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY tests/ ./tests/

# Create log directory
RUN mkdir -p logs

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "-m", "src.backend.main"]
