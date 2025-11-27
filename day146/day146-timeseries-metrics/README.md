# Day 146: Time Series Database Integration

Production-ready metrics extraction and storage system using TimescaleDB.

## Quick Start

```bash
# Build project
./build.sh

# Start TimescaleDB
docker-compose up -d timescaledb

# Run demo
./demo.sh

# Start all services
./start.sh
```

## Architecture

- **Metrics Extractor**: Parses logs and extracts time series metrics
- **Batch Writer**: Efficiently writes metrics to TimescaleDB
- **Query API**: FastAPI endpoints for metric queries
- **React Dashboard**: Real-time visualization

## API Endpoints

- `GET /metrics/response-time` - Response time metrics
- `GET /metrics/error-rate` - Error rate metrics
- `GET /metrics/resource-usage` - Resource usage metrics
- `GET /metrics/throughput` - Throughput metrics
- `GET /metrics/summary` - Overall summary

## Testing

```bash
source venv/bin/activate
pytest tests/ -v
```

## Docker Deployment

```bash
docker-compose up --build
```

Services:
- TimescaleDB: `localhost:5432`
- API: `http://localhost:8000`
- Dashboard: `http://localhost:3000`
