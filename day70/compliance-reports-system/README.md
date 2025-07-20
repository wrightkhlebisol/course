# Compliance Reports System

A comprehensive automated compliance reporting system for distributed log processing with support for multiple compliance frameworks including SOX, HIPAA, PCI-DSS, and GDPR.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.8+ (for manual mode)
- Node.js 16+ (for manual mode)
- `jq` for JSON formatting (optional, for demo)

### Starting the System

```bash
# Start with Docker (recommended)
./start.sh

# Start manually (without Docker)
./start.sh --no-docker

# Start and run demo automatically
./start.sh --demo
```

### Stopping the System

```bash
# Stop the system
./stop.sh

# Stop and clean up resources
./stop.sh --clean
```

### Running the Demo

```bash
# Run the interactive demo
./demo.sh
```

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   Port: 6379    │
                       └─────────────────┘
```

## 🎬 Demo Features

The demo showcases the following capabilities:

### 1. Dashboard Overview
- Real-time system statistics
- Recent compliance reports
- Framework-specific metrics
- Quick action buttons

### 2. Report Generation
- **SOX Compliance**: Financial reporting controls
- **HIPAA Compliance**: Healthcare data privacy
- **PCI-DSS Compliance**: Payment card security
- **GDPR Compliance**: Data protection regulation

### 3. Export Formats
- PDF reports with professional formatting
- CSV data exports for analysis
- JSON structured data
- XML compliance documents

### 4. Advanced Features
- Cryptographic signature verification
- Background report processing
- Scheduled report automation
- Real-time status monitoring

## 📋 Supported Compliance Frameworks

| Framework | Description | Retention Period | Key Features |
|-----------|-------------|------------------|--------------|
| **SOX** | Sarbanes-Oxley Act | 7 years | Financial controls, audit trails |
| **HIPAA** | Healthcare Privacy | 6 years | Patient data protection, access logs |
| **PCI-DSS** | Payment Security | 1 year | Cardholder data, security events |
| **GDPR** | Data Protection | 3 years | Personal data, consent management |

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - System information
- `GET /frameworks` - Available compliance frameworks
- `GET /dashboard/stats` - Dashboard statistics

### Report Management
- `POST /reports/generate` - Generate new report
- `GET /reports` - List all reports
- `GET /reports/{id}` - Get report details
- `GET /reports/{id}/download` - Download report file

### Scheduling
- `POST /reports/schedule` - Schedule automated reports
- `GET /reports/schedule` - List scheduled reports
- `DELETE /reports/schedule/{id}` - Delete scheduled report

## 🎯 Demo Scripts

### `start.sh`
Comprehensive startup script with the following features:

- **Docker Mode**: Uses Docker Compose for containerized deployment
- **Manual Mode**: Direct service startup for development
- **Port Checking**: Ensures ports are available before starting
- **Health Checks**: Verifies services are running properly
- **Auto Demo**: Optional automatic demo execution

```bash
# Basic startup
./start.sh

# Manual mode (no Docker)
./start.sh --no-docker

# Start with demo
./start.sh --demo
```

### `stop.sh`
Graceful shutdown script with cleanup:

- **Process Management**: Properly terminates running services
- **Port Cleanup**: Ensures ports are freed
- **Resource Cleanup**: Optional Docker resource cleanup
- **Verification**: Confirms services are stopped

```bash
# Basic stop
./stop.sh

# Stop with cleanup
./stop.sh --clean
```

### `demo.sh`
Interactive demonstration script:

- **Service Verification**: Checks if system is running
- **Browser Integration**: Opens relevant URLs automatically
- **Step-by-Step Guide**: Walks through all features
- **API Testing**: Demonstrates API functionality
- **Report Generation**: Creates sample reports

```bash
# Run interactive demo
./demo.sh
```

## 📁 Project Structure

```
compliance-reports-system/
├── start.sh                 # System startup script
├── stop.sh                  # System shutdown script
├── demo.sh                  # Interactive demo script
├── docker-compose.yml       # Docker configuration
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # API server
│   │   ├── services/       # Business logic
│   │   └── models/         # Data models
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/         # Dashboard pages
│   │   └── components/    # UI components
│   └── package.json       # Node.js dependencies
└── scripts/               # Utility scripts
    ├── demo.py           # Python demo automation
    └── build.sh          # Build utilities
```

## 🚀 Usage Examples

### 1. Quick Demo
```bash
# Start system and run demo
./start.sh --demo
```

### 2. Development Mode
```bash
# Start manually for development
./start.sh --no-docker

# Make changes...

# Stop system
./stop.sh
```

### 3. Production Deployment
```bash
# Start with Docker
./start.sh

# Monitor logs
docker-compose logs -f

# Stop and cleanup
./stop.sh --clean
```

### 4. Interactive Demo
```bash
# Start system first
./start.sh

# Run interactive demo
./demo.sh
```

## 🔍 Monitoring and Logs

### Log Files
- `logs/backend.log` - Backend application logs
- `logs/frontend.log` - Frontend application logs

### Docker Logs
```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Checks
- Backend: `http://localhost:8000/`
- Frontend: `http://localhost:3000`
- API Docs: `http://localhost:8000/docs`

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :3000
   
   # Kill process if needed
   kill -9 <PID>
   ```

2. **Docker Issues**
   ```bash
   # Clean up Docker
   docker-compose down --volumes
   docker system prune -f
   ```

3. **Permission Issues**
   ```bash
   # Make scripts executable
   chmod +x start.sh stop.sh demo.sh
   ```

### Manual Service Startup
```bash
# Backend
cd backend
source venv/bin/activate
python app/main.py

# Frontend (new terminal)
cd frontend
npm start
```

## 📚 Learning Outcomes

This project demonstrates:

- **Multi-framework Compliance Engine**: Support for SOX, HIPAA, PCI-DSS, GDPR
- **Automated Report Generation**: Background processing with status tracking
- **Cryptographic Integrity**: Digital signatures for report verification
- **Modern Web Dashboard**: React with Material-UI components
- **RESTful API Design**: FastAPI with comprehensive documentation
- **Container Orchestration**: Docker Compose for deployment
- **Scheduled Automation**: Background task scheduling
- **Export Flexibility**: Multiple format support (PDF, CSV, JSON, XML)

## 🎉 Getting Started

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd compliance-reports-system
   ```

2. **Start the System**
   ```bash
   ./start.sh
   ```

3. **Run the Demo**
   ```bash
   ./demo.sh
   ```

4. **Explore the Dashboard**
   - Open: http://localhost:3000
   - API Docs: http://localhost:8000/docs

5. **Stop the System**
   ```bash
   ./stop.sh
   ```

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review the API documentation
- Examine the log files
- Use the demo scripts for testing

---

**Happy Compliance Reporting! 🎯📊** 