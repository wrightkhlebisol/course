"""
FastAPI application for metrics export system.
Exposes metrics endpoints and management API.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from contextlib import asynccontextmanager
import asyncio
from typing import Dict, Any

from src.metrics.registry import global_registry
from src.exporters.prometheus_exporter import PrometheusExporter
from src.exporters.datadog_exporter import DatadogExporter
from src.exporters.export_manager import MetricsExportManager
from src.collectors.system_metrics import SystemMetricsCollector
from src.collectors.app_metrics import AppMetricsCollector
import structlog
import os

logger = structlog.get_logger()

# Background tasks
background_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("application_starting")
    
    # Start metric collection
    collection_task = asyncio.create_task(collect_metrics_loop())
    background_tasks.append(collection_task)
    
    # Start export loop
    await app.state.export_manager.start_export_loop()
    
    yield
    
    # Shutdown
    logger.info("application_stopping")
    await app.state.export_manager.stop_export_loop()
    
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="Metrics Export System",
    description="Day 141: Metrics export to Prometheus and Datadog",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize exporters
prometheus_exporter = PrometheusExporter(global_registry)

datadog_api_key = os.getenv("DATADOG_API_KEY", "test_key")
datadog_app_key = os.getenv("DATADOG_APP_KEY", "test_key")
datadog_enabled = os.getenv("DATADOG_ENABLED", "false").lower() in ("true", "1", "yes")
datadog_exporter = None

# Enable Datadog if API key is set (not test_key) OR if explicitly enabled via env var
if datadog_api_key != "test_key" or datadog_enabled:
    try:
        datadog_exporter = DatadogExporter(datadog_api_key, datadog_app_key)
        logger.info("datadog_exporter_initialized", enabled=True)
    except Exception as e:
        logger.warning("datadog_exporter_init_failed", error=str(e), 
                      note="Datadog will remain disabled")

# Initialize collectors
system_collector = SystemMetricsCollector(global_registry)
app_collector = AppMetricsCollector(global_registry)

# Initialize export manager
export_manager = MetricsExportManager(
    global_registry,
    prometheus_exporter,
    datadog_exporter
)

app.state.export_manager = export_manager
app.state.system_collector = system_collector
app.state.app_collector = app_collector

async def collect_metrics_loop():
    """Background loop to collect metrics"""
    while True:
        try:
            # Collect system metrics
            system_collector.collect()
            
            # Simulate application activity
            app_collector.simulate_activity()
            
            await asyncio.sleep(10)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("metrics_collection_error", error=str(e))
            await asyncio.sleep(5)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Metrics Export System",
        "version": "1.0.0",
        "endpoints": {
            "metrics": "/metrics",
            "health": "/health",
            "stats": "/api/stats"
        }
    }

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return prometheus_exporter.get_metrics()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """Get current statistics"""
    return {
        "collectors": {
            "system": system_collector.collect(),
            "application": app_collector.get_counters(),
            "queues": app_collector.get_queue_depths()
        },
        "export": export_manager.get_export_stats(),
        "cardinality": global_registry.check_cardinality()
    }

@app.post("/api/trigger-export")
async def trigger_export():
    """Manually trigger metrics export"""
    try:
        results = await export_manager.export_metrics()
        return {"success": True, "results": results}
    except Exception as e:
        logger.error("manual_export_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Metrics dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metrics Export Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                background: #f5f7fa;
                min-height: 100vh;
                padding: 24px;
                color: #1a202c;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .header {
                background: #ffffff;
                padding: 32px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
                margin-bottom: 24px;
                border: 1px solid #e2e8f0;
            }
            .header h1 {
                color: #1a202c;
                margin-bottom: 8px;
                font-size: 28px;
                font-weight: 700;
                letter-spacing: -0.5px;
            }
            .header p {
                color: #64748b;
                font-size: 15px;
                margin-bottom: 0;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 24px;
            }
            .metric-card {
                background: #ffffff;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
                border: 1px solid #e2e8f0;
                transition: all 0.2s ease;
            }
            .metric-card:hover {
                box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
                transform: translateY(-1px);
            }
            .metric-value {
                font-size: 32px;
                font-weight: 700;
                color: #0f172a;
                margin: 12px 0 4px 0;
                letter-spacing: -0.5px;
            }
            .metric-label {
                color: #64748b;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 600;
            }
            .chart-container {
                background: #ffffff;
                padding: 28px;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
                margin-bottom: 20px;
                border: 1px solid #e2e8f0;
            }
            .chart-container canvas {
                max-height: 400px;
                height: 400px !important;
            }
            .chart-container h3 {
                margin-bottom: 24px;
                color: #1a202c;
                font-size: 18px;
                font-weight: 600;
                letter-spacing: -0.3px;
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
            }
            .status-online { 
                background: #10b981;
                box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
            }
            .status-offline { 
                background: #ef4444;
                box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
            }
            .export-status {
                display: flex;
                gap: 16px;
                margin-top: 20px;
                flex-wrap: wrap;
            }
            .export-badge {
                background: #f8fafc;
                padding: 10px 16px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                border: 1px solid #e2e8f0;
                font-size: 14px;
                color: #475569;
                font-weight: 500;
            }
            button {
                background: #0f172a;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s ease;
                letter-spacing: 0.3px;
            }
            button:hover {
                background: #1e293b;
                transform: translateY(-1px);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            button:active {
                transform: translateY(0);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Metrics Export Dashboard</h1>
                <p>Real-time monitoring of metrics export to Prometheus and Datadog</p>
                <div class="export-status">
                    <div class="export-badge">
                        <span class="status-indicator status-online"></span>
                        <span>Prometheus: Active</span>
                    </div>
                    <div class="export-badge">
                        <span class="status-indicator" id="datadog-status"></span>
                        <span id="datadog-text">Datadog: Checking...</span>
                    </div>
                    <button onclick="triggerExport()">Export Now</button>
                </div>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Messages Processed</div>
                    <div class="metric-value" id="messages-processed">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Messages Failed</div>
                    <div class="metric-value" id="messages-failed">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">CPU Usage</div>
                    <div class="metric-value" id="cpu-usage">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Memory Usage</div>
                    <div class="metric-value" id="memory-usage">0%</div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Message Processing Rate</h3>
                <canvas id="messageChart"></canvas>
            </div>
            
            <div class="chart-container">
                <h3>Queue Depths</h3>
                <canvas id="queueChart"></canvas>
            </div>
        </div>
        
        <script>
            let messageChart, queueChart;
            let messageData = [];
            let queueData = {
                high_priority: [],
                normal: [],
                low_priority: []
            };
            
            function initCharts() {
                const messageCtx = document.getElementById('messageChart').getContext('2d');
                messageChart = new Chart(messageCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Messages Processed',
                            data: [],
                            borderColor: '#14b8a6',
                            backgroundColor: 'rgba(20, 184, 166, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true,
                            pointRadius: 3,
                            pointHoverRadius: 5
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                                labels: {
                                    usePointStyle: true,
                                    padding: 15,
                                    font: {
                                        size: 13,
                                        weight: '500'
                                    }
                                }
                            }
                        },
                        scales: {
                            y: { 
                                beginAtZero: true,
                                grid: {
                                    color: '#f1f5f9'
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: {
                                        size: 12
                                    }
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: {
                                        size: 12
                                    }
                                }
                            }
                        }
                    }
                });
                
                const queueCtx = document.getElementById('queueChart').getContext('2d');
                queueChart = new Chart(queueCtx, {
                    type: 'bar',
                    data: {
                        labels: ['High Priority', 'Normal', 'Low Priority'],
                        datasets: [{
                            label: 'Queue Depth',
                            data: [0, 0, 0],
                            backgroundColor: [
                                '#dc2626',
                                '#f59e0b',
                                '#10b981'
                            ],
                            borderRadius: 6,
                            borderSkipped: false
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: { 
                                beginAtZero: true,
                                grid: {
                                    color: '#f1f5f9'
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: {
                                        size: 12
                                    }
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    color: '#64748b',
                                    font: {
                                        size: 12,
                                        weight: '500'
                                    }
                                }
                            }
                        }
                    }
                });
            }
            
            async function updateMetrics() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    
                    // Update metric cards
                    document.getElementById('messages-processed').textContent = 
                        data.collectors.application.messages_processed;
                    document.getElementById('messages-failed').textContent = 
                        data.collectors.application.messages_failed;
                    document.getElementById('cpu-usage').textContent = 
                        data.collectors.system.cpu_percent.toFixed(1) + '%';
                    document.getElementById('memory-usage').textContent = 
                        data.collectors.system.memory_percent.toFixed(1) + '%';
                    
                    // Update Datadog status
                    const datadogEnabled = data.export.backends_configured.datadog;
                    document.getElementById('datadog-status').className = 
                        'status-indicator ' + (datadogEnabled ? 'status-online' : 'status-offline');
                    document.getElementById('datadog-text').textContent = 
                        'Datadog: ' + (datadogEnabled ? 'Active' : 'Disabled');
                    
                    // Update message chart
                    const time = new Date().toLocaleTimeString();
                    messageChart.data.labels.push(time);
                    messageChart.data.datasets[0].data.push(data.collectors.application.messages_processed);
                    
                    if (messageChart.data.labels.length > 20) {
                        messageChart.data.labels.shift();
                        messageChart.data.datasets[0].data.shift();
                    }
                    
                    messageChart.update('none');
                    
                    // Update queue chart
                    if (data.collectors.queues) {
                        const queues = data.collectors.queues;
                        queueChart.data.datasets[0].data = [
                            queues.high_priority || 0,
                            queues.normal || 0,
                            queues.low_priority || 0
                        ];
                        queueChart.update('none');
                    }
                    
                } catch (error) {
                    console.error('Failed to update metrics:', error);
                }
            }
            
            async function triggerExport() {
                try {
                    const response = await fetch('/api/trigger-export', { method: 'POST' });
                    const data = await response.json();
                    alert('Export triggered successfully!');
                } catch (error) {
                    alert('Export failed: ' + error.message);
                }
            }
            
            // Initialize
            initCharts();
            updateMetrics();
            setInterval(updateMetrics, 5000);
        </script>
    </body>
    </html>
    """
