# Day 68: Automated Data Retention Policies

## 🎯 Project Overview

This project implements an automated data retention system with compliance management capabilities. The system provides policy-driven log retention, multi-tier storage management, and regulatory compliance monitoring.

## 🚀 Features

### Core Functionality
- **Policy-Driven Retention**: Configurable retention policies based on log source, level, and category
- **Multi-Tier Storage**: Hot, warm, and cold storage tiers for optimal performance and cost
- **Compliance Framework**: GDPR, SOX, and HIPAA compliance monitoring
- **Automated Processing**: Background log processing and retention actions
- **Real-time Metrics**: Live monitoring of system performance and storage usage

### API Endpoints
- **Retention Management**: `/api/retention/` - Policy management and log processing
- **Compliance Monitoring**: `/api/compliance/` - Compliance status and reporting
- **Storage Management**: `/api/storage/` - Multi-tier storage operations
- **Health Monitoring**: `/health` - System health checks
- **Metrics**: `/metrics` - System performance metrics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Policy Engine  │    │ Storage Manager │
│   (Port 8000)   │◄──►│                 │◄──►│                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  API Routes     │    │ Compliance      │    │ Multi-Tier      │
│  - Retention    │    │ Engine          │    │ Storage         │
│  - Compliance   │    │ - GDPR          │    │ - Hot           │
│  - Storage      │    │ - SOX           │    │ - Warm          │
└─────────────────┘    │ - HIPAA         │    │ - Cold          │
                       └─────────────────┘    └─────────────────┘
```

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+
- pip
- curl (for testing)

### Quick Start
```bash
# Clone and navigate to project
cd day68-retention-system

# Start the system
./start.sh

# Run demo
./demo.sh

# Stop the system
./stop.sh
```

## 🔧 Usage

### Starting the System
```bash
./start.sh
```
This will:
- Create a Python virtual environment
- Install dependencies
- Initialize storage directories
- Start the FastAPI backend on port 8000

### Running the Demo
```bash
./demo.sh
```
This demonstrates all system features including:
- Policy management
- Compliance monitoring
- Storage operations
- Real-time metrics

### Stopping the System
```bash
./stop.sh
```
This gracefully stops all services and cleans up processes.

## 🌐 API Access

Once running, access the system at:

- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Retention API**: http://localhost:8000/api/retention/
- **Compliance API**: http://localhost:8000/api/compliance/
- **Storage API**: http://localhost:8000/api/storage/

## 📋 Sample API Calls

### Get All Retention Policies
```bash
curl http://localhost:8000/api/retention/
```

### Get Compliance Status
```bash
curl http://localhost:8000/api/compliance/
```

### Get Storage Status
```bash
curl http://localhost:8000/api/storage/
```

### Process Logs
```bash
curl -X POST http://localhost:8000/api/retention/process \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "log_001",
      "timestamp": "2024-01-15T10:00:00Z",
      "level": "info",
      "source": "application",
      "category": "general",
      "content": "Sample log message"
    }
  ]'
```

## 📊 Policy Configuration

The system includes three sample retention policies:

1. **Application Logs (30 days)**: Deletes debug/info logs after 30 days
2. **Security Logs (7 years)**: Archives warning/error security logs for 7 years
3. **Financial Logs (7 years)**: Archives financial category logs for 7 years

## 🏛️ Compliance Frameworks

### GDPR (General Data Protection Regulation)
- **Status**: Compliant (98.0% score)
- **Requirements**: Data minimization, right to erasure, consent management
- **Last Audit**: 2024-01-15

### SOX (Sarbanes-Oxley Act)
- **Status**: Compliant (92.0% score)
- **Requirements**: 7-year retention for financial records
- **Last Audit**: 2024-01-10

### HIPAA (Health Insurance Portability and Accountability Act)
- **Status**: Not Applicable
- **Requirements**: Protected health information handling
- **Last Audit**: N/A

## 💾 Storage Tiers

### Hot Storage
- **Path**: `/tmp/logs/hot`
- **Purpose**: Frequently accessed recent logs
- **Retention**: Short-term (hours to days)

### Warm Storage
- **Path**: `/tmp/logs/warm`
- **Purpose**: Moderately accessed logs
- **Retention**: Medium-term (days to months)

### Cold Storage
- **Path**: `/tmp/logs/cold`
- **Purpose**: Rarely accessed archived logs
- **Retention**: Long-term (months to years)

## 🔍 Monitoring & Metrics

The system provides real-time metrics including:
- Total policies configured
- Logs processed today
- Logs deleted/archived today
- Storage space saved
- Compliance scores by framework

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

## 📁 Project Structure

```
day68-retention-system/
├── src/
│   ├── api/
│   │   └── routes.py          # API route definitions
│   ├── compliance/
│   │   └── ...                # Compliance engine
│   ├── models/
│   │   └── ...                # Data models
│   ├── retention/
│   │   └── ...                # Retention engine
│   ├── storage/
│   │   └── ...                # Storage management
│   ├── utils/
│   │   └── logger.py          # Logging utilities
│   └── main.py                # FastAPI application entry point
├── tests/
│   └── ...                    # Test files
├── scripts/
│   ├── init_db.py             # Database initialization
│   └── ...                    # Utility scripts
├── config/
│   └── ...                    # Configuration files
├── docs/
│   └── ...                    # Documentation
├── start.sh                   # Start script
├── stop.sh                    # Stop script
├── demo.sh                    # Demo script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Next Steps

This system is ready for Day 69: GDPR Compliance Features, which will include:
- Enhanced data anonymization
- Right to erasure implementation
- Consent management
- Data portability features
- Enhanced audit trails

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is part of the System Design Course curriculum.

---

**Day 68 Complete!** 🎉 The automated data retention system is now operational with policy-driven management, compliance monitoring, and multi-tier storage capabilities. 