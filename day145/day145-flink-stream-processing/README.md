# Day 145: Real-Time Stream Processing with Apache Flink

Production-ready stream processing system with complex event detection.

## Quick Start

### Native Setup
```bash
./build.sh      # Build and test
./start.sh      # Start system and run demo
./stop.sh       # Stop all components
```

### Docker Setup
```bash
docker-compose up --build
```

## Access Points

- **Dashboard**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **Metrics**: http://localhost:9090/metrics

## Features

- ✅ Authentication spike detection
- ✅ Latency degradation detection  
- ✅ Cascading failure detection
- ✅ Real-time web dashboard
- ✅ Exactly-once processing semantics
- ✅ Fault-tolerant checkpointing

## Architecture

The system implements Flink-style stream processing with:
- Event time processing
- Windowed aggregations
- Stateful pattern detection
- Real-time alerting

## Testing

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Performance

- Throughput: 1000+ events/second
- Latency: <100ms p99
- Memory: ~200MB base
