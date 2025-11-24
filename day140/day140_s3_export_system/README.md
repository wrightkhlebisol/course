# Day 140: S3/Blob Storage Export System

Automated export system for distributed log processing with cloud storage integration.

## Features

- ✅ Automated scheduled exports to S3-compatible storage
- ✅ Smart data partitioning (date/service/level)
- ✅ Multiple format support (Parquet, JSON, CSV)
- ✅ Compression (GZIP, ZSTD)
- ✅ Metadata tracking and export history
- ✅ Real-time web dashboard
- ✅ RESTful API
- ✅ Docker support with MinIO

## Quick Start

```bash
# Build and test
./build.sh

# Run demonstration
./demo.sh

# Start system
./start.sh

# Stop system
./stop.sh
```

## Docker Deployment

```bash
# Start with MinIO
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## API Endpoints

- `GET /` - API root
- `POST /api/export/manual` - Trigger manual export
- `GET /api/export/status` - Get system status
- `GET /api/export/history` - Get export history
- `GET /api/storage/objects` - List storage objects
- `GET /health` - Health check

## Web Dashboard

Access the interactive dashboard at http://localhost:8000

## Configuration

Edit `config/config.yaml` to customize:
- Storage provider (S3, MinIO, local)
- Export schedule (cron format)
- Compression and format options
- Partitioning scheme

## Testing

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Architecture

- FastAPI backend with async support
- React dashboard with real-time updates
- APScheduler for reliable job scheduling
- Boto3 for S3 operations
- SQLAlchemy for metadata tracking
- Parquet/Pandas for efficient data processing

## Production Considerations

- Use IAM roles instead of access keys
- Enable server-side encryption
- Configure lifecycle policies
- Monitor export metrics
- Set up alerting for failures

## License

MIT License - Part of 254-Day System Design Series
