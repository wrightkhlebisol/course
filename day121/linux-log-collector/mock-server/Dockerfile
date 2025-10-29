FROM python:3.11-slim

WORKDIR /app

# Install aiohttp
RUN pip install --no-cache-dir aiohttp

# Copy server script
COPY server.py .

# Set environment variable for port (mapped to 8080 on host)
ENV SERVER_PORT=8000

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]

