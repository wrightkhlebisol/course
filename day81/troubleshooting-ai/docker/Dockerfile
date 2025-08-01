FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose ports
EXPOSE 8000 5000

# Create startup script
RUN echo '#!/bin/bash\n\
uvicorn src.api.recommendation_service:app --host 0.0.0.0 --port 8000 &\n\
cd src/web && python dashboard.py\n\
' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
