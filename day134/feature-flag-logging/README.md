# Feature Flag Status Logging System

A comprehensive feature flag management system with automatic status logging, built for Day 134 of the 254-Day System Design Series.

## 🎯 Features

- **Feature Flag Management**: Create, update, delete, and evaluate feature flags
- **Automatic Logging**: All flag interactions are automatically logged
- **Real-time Dashboard**: Monitor flag status and activity in real-time
- **Audit Trail**: Complete history of all flag changes and evaluations
- **High Performance**: Redis caching with database persistence
- **Scalable Architecture**: Designed for distributed systems

## 🏗️ Architecture

### Backend (Python 3.11 + FastAPI)
- **FastAPI**: Modern web framework for APIs
- **SQLAlchemy**: Database ORM with PostgreSQL
- **Redis**: High-performance caching and metrics
- **RabbitMQ**: Message queue for distributed logging
- **Structured Logging**: JSON-based logging for observability

### Frontend (React 18)
- **React**: Modern UI framework with hooks
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Data fetching and caching
- **Recharts**: Beautiful charts for analytics
- **React Router**: Client-side routing

### Infrastructure
- **PostgreSQL**: Primary database for flag storage
- **Redis**: Caching and real-time metrics
- **RabbitMQ**: Message broker for event streaming
- **Docker**: Containerized deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Build the System
```bash
./build.sh
```

### 2. Start All Services
```bash
./start.sh
```

### 3. Run Tests
```bash
./test.sh
```

### 4. View Demo
```bash
./demo.sh
```

### 5. Stop Services
```bash
./stop.sh
```

## 🌐 Access URLs

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 📊 API Endpoints

### Feature Flags
- `GET /api/v1/flags` - List all flags
- `POST /api/v1/flags` - Create new flag
- `PUT /api/v1/flags/{id}` - Update existing flag
- `DELETE /api/v1/flags/{id}` - Delete flag

### Flag Evaluation
- `POST /api/v1/flags/evaluate` - Evaluate flag for user context

### Audit Logs
- `GET /api/v1/logs/recent` - Get recent activity logs
- `GET /api/v1/flags/{name}/logs` - Get logs for specific flag

## 🧪 Testing

The system includes comprehensive testing:
- **Unit Tests**: Test individual components
- **Integration Tests**: Test API endpoints
- **Load Tests**: Performance validation

## 📝 Usage Examples

### Create Feature Flag
```bash
curl -X POST http://localhost:8000/api/v1/flags \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_feature",
    "description": "Enable new feature",
    "enabled": true,
    "rollout_percentage": "50",
    "target_groups": ["beta-users"]
  }'
```

### Evaluate Flag
```bash
curl -X POST http://localhost:8000/api/v1/flags/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "flag_name": "new_feature",
    "user_context": {"user_id": "user123", "group": "beta-users"},
    "default_value": false
  }'
```

## 🔧 Configuration

### Backend Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- Environment variables in `docker-compose.yml`

### Frontend Configuration
- `REACT_APP_API_URL`: Backend API URL
- Vite configuration in `vite.config.js`

## 📈 Monitoring & Observability

The system provides comprehensive observability:
- **Structured Logs**: JSON-formatted logs for analysis
- **Metrics Collection**: Flag evaluation counts and timing
- **Event Streaming**: All changes published to message queue
- **Real-time Dashboard**: Live monitoring of system activity

## 🏢 Production Considerations

- **Security**: Implement authentication and authorization
- **Scaling**: Use load balancers and multiple instances
- **Monitoring**: Add external monitoring (Prometheus, Grafana)
- **Backup**: Regular database and configuration backups

## 📚 Further Reading

This implementation demonstrates patterns used in production systems like:
- LaunchDarkly's feature flag service
- Facebook's GateKeeper system
- Netflix's feature rollout infrastructure

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is part of the 254-Day System Design Series.
