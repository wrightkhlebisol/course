FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY web/ ./web/
COPY scripts/ ./scripts/

# Create directories
RUN mkdir -p checkpoints logs

EXPOSE 8080 8765

CMD ["python", "src/main.py"]
