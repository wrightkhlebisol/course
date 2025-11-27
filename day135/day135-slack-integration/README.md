# Day 135: Slack Notification Integration

Real-time Slack notifications for distributed log processing systems.

## Quick Start

1. **Configure Slack**: Update `.env` with your Slack credentials
2. **Build**: `./build.sh`
3. **Start**: `./start.sh`
4. **Demo**: `python demo.py`

## Features

- Real-time alert routing to Slack channels
- Intelligent deduplication and rate limiting
- Interactive message components
- Multi-severity alert handling
- Modern React dashboard
- Comprehensive testing suite

## Architecture

- **Backend**: FastAPI + Slack SDK
- **Frontend**: React + Material-UI
- **Storage**: Redis for caching and queuing
- **Deployment**: Docker + Docker Compose

## Configuration

Update `.env` file with your Slack app credentials:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Testing

```bash
python -m pytest tests/ -v
```

## Monitoring

- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
