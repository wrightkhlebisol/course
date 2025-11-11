# Database Audit Log Collection System

## Overview
A comprehensive database audit log collection system that captures and analyzes security events from PostgreSQL, MySQL, MongoDB, and SQL Server databases.

## Features
- Multi-database audit log collection
- Real-time security threat detection
- Modern web dashboard with live updates
- Compliance monitoring (SOX, HIPAA, GDPR, PCI DSS)
- Connection pooling and error handling

## Quick Start

### 1. Build the system
```bash
./build.sh
```

### 2. Start services
```bash
./start.sh
```

### 3. Access dashboard
Open http://localhost:8080 in your browser

### 4. Run demo
```bash
./demo.sh
```

## Architecture
- **Database Connectors**: Specialized collectors for each database type
- **Log Parsers**: Normalize different audit log formats
- **Security Detector**: Real-time threat analysis
- **Web Dashboard**: Modern UI with live metrics

## Testing
```bash
python -m pytest tests/ -v
```

## Docker Deployment
```bash
docker-compose up -d
```

## Configuration
Edit `config/database_config.yaml` to configure:
- Database connections
- Security thresholds
- Collector settings
- Dashboard options
