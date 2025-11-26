# Day 143: Apache Spark Integration for Big Data Log Processing

Production-ready Apache Spark integration for distributed log analytics.

## Features

- ⚡ Distributed log processing with Apache Spark
- 📊 Real-time analytics dashboard
- 🔍 Error rate and performance analysis
- 🎯 Anomaly detection
- 📈 Correlation analysis
- 🌐 REST API for job management

## Quick Start

### Build and Run

```bash
# Build the project
./build.sh

# Start the application
./start.sh

# Run demonstration
source venv/bin/activate
python scripts/demo.py

# Stop the application
./stop.sh
```

### Docker Deployment

```bash
cd docker
docker-compose up --build
```

## API Endpoints

- `GET /health` - Health check
- `GET /cluster/info` - Spark cluster information
- `POST /analyze` - Run log analysis
- `GET /jobs/history` - Job execution history
- `GET /results/{type}` - Analysis results

## Dashboard

Open `src/dashboard/index.html` in your browser for real-time monitoring.

## Testing

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Performance

- Processes 1M+ logs in under 30 seconds
- Supports distributed processing across multiple nodes
- In-memory computing for fast iterative analytics

## Integration

Connects with:
- Elasticsearch (Day 142)
- Metrics systems (Day 141)
- Machine Learning pipeline (Day 144)
