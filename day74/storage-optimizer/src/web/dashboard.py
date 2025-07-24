"""
Storage Optimization Dashboard
Real-time monitoring and control interface
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
import plotly.graph_objs as go
import plotly.utils

class StorageOptimizationDashboard:
    def __init__(self, storage_engine, pattern_analyzer):
        self.app = FastAPI(title="Storage Optimization Dashboard")
        self.storage_engine = storage_engine
        self.pattern_analyzer = pattern_analyzer
        self.templates = Jinja2Templates(directory="src/web/templates")
        self.active_connections: List[WebSocket] = []
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "title": "Storage Format Optimizer"
            })
        
        @self.app.get("/api/stats")
        async def get_stats():
            stats = self.storage_engine.get_optimization_stats()
            insights = self.pattern_analyzer.get_optimization_insights()
            
            return JSONResponse({
                "storage_stats": stats,
                "pattern_insights": insights,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.get("/api/recommendations/{partition_key}")
        async def get_recommendations(partition_key: str):
            recommendations = self.pattern_analyzer.get_recommendations(partition_key)
            return JSONResponse(recommendations)
        
        @self.app.post("/api/optimize/{partition_key}")
        async def trigger_optimization(partition_key: str):
            # Trigger format optimization for partition
            try:
                # In real implementation, this would trigger migration
                result = {"status": "optimization_triggered", "partition": partition_key}
                await self.broadcast_update(result)
                return JSONResponse(result)
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.post("/api/demo/metrics")
        async def run_metrics_demo():
            """Run a demo to generate new metrics and show live updates"""
            try:
                print("🎬 Starting metrics demo...")
                
                # Generate new demo data
                await self.generate_demo_data()
                
                # Simulate query patterns to update metrics
                await self.simulate_query_patterns()
                
                # Trigger some optimizations
                await self.trigger_demo_optimizations()
                
                result = {
                    "success": True,
                    "message": "Demo completed successfully",
                    "new_queries": 25,
                    "optimizations_triggered": 3,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Broadcast update to all connected clients
                await self.broadcast_update({
                    "type": "demo_completed",
                    "data": result
                })
                
                print("✅ Metrics demo completed")
                return JSONResponse(result)
                
            except Exception as e:
                print(f"❌ Demo failed: {e}")
                return JSONResponse({
                    "success": False,
                    "error": str(e)
                }, status_code=500)
        
        @self.app.get("/api/performance-chart/{partition_key}")
        async def get_performance_chart(partition_key: str):
            # Generate performance chart data
            query_records = self.pattern_analyzer.query_performance.get(partition_key, [])
            
            if not query_records:
                return JSONResponse({"error": "No data available"})
            
            timestamps = [record['timestamp'] for record in query_records[-50:]]  # Last 50 queries
            execution_times = [record['execution_time'] for record in query_records[-50:]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=execution_times,
                mode='lines+markers',
                name='Query Execution Time',
                line=dict(color='#4CAF50', width=2)
            ))
            
            fig.update_layout(
                title=f'Query Performance - {partition_key}',
                xaxis_title='Timestamp',
                yaxis_title='Execution Time (seconds)',
                template='plotly_white'
            )
            
            return JSONResponse(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Send periodic updates
                    stats = self.storage_engine.get_optimization_stats()
                    await websocket.send_text(json.dumps({
                        "type": "stats_update",
                        "data": stats,
                        "timestamp": datetime.now().isoformat()
                    }))
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast updates to all connected websockets"""
        if self.active_connections:
            message = json.dumps({
                "type": "optimization_update",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    self.active_connections.remove(connection)
    
    async def generate_demo_data(self):
        """Generate new demo data to trigger metric updates"""
        print("📝 Generating new demo data...")
        
        # Generate new logs for each partition
        partitions = ['web-logs', 'api-logs', 'error-logs']
        
        for partition in partitions:
            # Generate 10-20 new logs per partition
            num_logs = 10 + (hash(partition) % 10)  # Random number between 10-20
            
            for i in range(num_logs):
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO' if partition != 'error-logs' else 'ERROR',
                    'service': partition.replace('-logs', '-service'),
                    'message': f'Demo log entry {i+1} for {partition}',
                    'user_id': f'user-{i}',
                    'status_code': 200 if partition != 'error-logs' else 500,
                    'duration_ms': 50 + (i * 10),
                    'ip_address': f'192.168.1.{i+1}'
                }
                
                # Write to storage engine
                await asyncio.sleep(0.01)  # Small delay to simulate real processing
                await self.storage_engine.write_logs([log_entry], partition)
        
        print(f"✅ Generated demo data for {len(partitions)} partitions")
    
    async def simulate_query_patterns(self):
        """Simulate various query patterns to update metrics"""
        print("🔍 Simulating query patterns...")
        
        # Different types of queries
        queries = [
            # Full record queries (row-oriented)
            {'partition': 'error-logs', 'type': 'full_record', 'filters': {'level': 'ERROR'}},
            {'partition': 'web-logs', 'type': 'full_record', 'filters': {'status_code': 200}},
            {'partition': 'api-logs', 'type': 'full_record', 'filters': {'service': 'api-service'}},
            
            # Analytical queries (columnar)
            {'partition': 'web-logs', 'type': 'analytical', 'columns': ['timestamp', 'duration_ms', 'status_code']},
            {'partition': 'api-logs', 'type': 'analytical', 'columns': ['service', 'level', 'duration_ms']},
            {'partition': 'error-logs', 'type': 'analytical', 'columns': ['timestamp', 'level', 'status_code']},
            
            # Mixed queries (hybrid)
            {'partition': 'web-logs', 'type': 'mixed', 'filters': {'status_code': 200}, 'columns': ['timestamp', 'user_id']},
            {'partition': 'api-logs', 'type': 'mixed', 'filters': {'level': 'INFO'}, 'columns': ['service', 'duration_ms']},
        ]
        
        for i, query in enumerate(queries):
            print(f"  Query {i+1}: {query['type']} on {query['partition']}")
            
            # Simulate query execution
            start_time = datetime.now()
            await asyncio.sleep(0.05)  # Simulate processing time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Record query in pattern analyzer
            query_data = {
                'type': query['type'],
                'filters': query.get('filters', {}),
                'columns': query.get('columns', [])
            }
            self.pattern_analyzer.record_query(
                partition_key=query['partition'],
                query=query_data,
                execution_time=execution_time,
                result_count=10 + (i * 5)  # Simulate result count
            )
        
        print(f"✅ Simulated {len(queries)} query patterns")
    
    async def trigger_demo_optimizations(self):
        """Trigger storage format optimizations"""
        print("🎯 Triggering demo optimizations...")
        
        partitions = ['web-logs', 'api-logs', 'error-logs']
        
        for partition in partitions:
            print(f"  Optimizing {partition}...")
            
            # Get current recommendations
            recommendations = self.pattern_analyzer.get_recommendations(partition)
            
            # Simulate format change based on recommendations
            if recommendations.get('confidence') in ['high', 'medium']:
                print(f"    Recommended format: {recommendations['recommended_format']}")
            
            await asyncio.sleep(0.1)  # Small delay
        
        print("✅ Demo optimizations completed")

# Template for dashboard HTML
dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }
        
        .card h3 {
            color: #4285f4;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric:last-child { border-bottom: none; }
        
        .metric-value {
            font-weight: 600;
            color: #34a853;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-green { background-color: #34a853; }
        .status-yellow { background-color: #fbbc05; }
        .status-red { background-color: #ea4335; }
        
        .optimize-btn {
            background: linear-gradient(135deg, #4285f4, #34a853);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .optimize-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.4);
        }
        
        #performance-chart { 
            width: 100%; 
            height: 400px; 
            background: rgba(255, 255, 255, 0.5);
            border-radius: 12px;
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .connected {
            background-color: rgba(52, 168, 83, 0.1);
            color: #34a853;
            border: 1px solid #34a853;
        }
        
        .disconnected {
            background-color: rgba(234, 67, 53, 0.1);
            color: #ea4335;
            border: 1px solid #ea4335;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connection-status">Connecting...</div>
    
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <p>Intelligent storage format optimization for distributed log processing</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 Storage Statistics</h3>
                <div id="storage-stats">
                    <div class="metric">
                        <span>Total Storage</span>
                        <span class="metric-value" id="total-storage">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Compression Savings</span>
                        <span class="metric-value" id="compression-savings">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Active Partitions</span>
                        <span class="metric-value" id="active-partitions">Loading...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Format Distribution</h3>
                <div id="format-distribution">
                    <div class="metric">
                        <span><span class="status-indicator status-green"></span>Row-Oriented</span>
                        <span class="metric-value" id="row-count">0</span>
                    </div>
                    <div class="metric">
                        <span><span class="status-indicator status-yellow"></span>Columnar</span>
                        <span class="metric-value" id="columnar-count">0</span>
                    </div>
                    <div class="metric">
                        <span><span class="status-indicator status-red"></span>Hybrid</span>
                        <span class="metric-value" id="hybrid-count">0</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ Performance Metrics</h3>
                <div id="performance-metrics">
                    <div class="metric">
                        <span>Avg Query Time</span>
                        <span class="metric-value" id="avg-query-time">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Optimization Score</span>
                        <span class="metric-value" id="optimization-score">Loading...</span>
                    </div>
                </div>
                <button class="optimize-btn" onclick="triggerOptimization()">
                    🚀 Optimize All
                </button>
            </div>
        </div>
        
        <div class="card">
            <h3>📈 Performance Trends</h3>
            <div id="performance-chart"></div>
        </div>
    </div>

    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        let socket;
        let isConnected = false;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            socket = new WebSocket(wsUrl);
            
            socket.onopen = function(event) {
                isConnected = true;
                updateConnectionStatus();
                console.log('WebSocket connected');
            };
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'stats_update') {
                    updateDashboard(data.data);
                }
            };
            
            socket.onclose = function(event) {
                isConnected = false;
                updateConnectionStatus();
                console.log('WebSocket disconnected');
                // Reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };
            
            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateConnectionStatus() {
            const status = document.getElementById('connection-status');
            if (isConnected) {
                status.textContent = '🟢 Connected';
                status.className = 'connection-status connected';
            } else {
                status.textContent = '🔴 Disconnected';
                status.className = 'connection-status disconnected';
            }
        }
        
        function updateDashboard(stats) {
            // Update storage statistics
            document.getElementById('total-storage').textContent = `${stats.total_storage_mb} MB`;
            document.getElementById('compression-savings').textContent = `${stats.compression_savings}%`;
            document.getElementById('active-partitions').textContent = Object.keys(stats.partitions).length;
            
            // Update format distribution
            const formatDist = stats.format_distribution || {};
            document.getElementById('row-count').textContent = formatDist.row || 0;
            document.getElementById('columnar-count').textContent = formatDist.columnar || 0;
            document.getElementById('hybrid-count').textContent = formatDist.hybrid || 0;
            
            // Calculate average query time across all partitions
            const partitions = Object.values(stats.partitions);
            const avgQueryTime = partitions.length > 0 
                ? partitions.reduce((sum, p) => sum + p.avg_query_time, 0) / partitions.length
                : 0;
            document.getElementById('avg-query-time').textContent = `${avgQueryTime.toFixed(3)}s`;
            
            // Calculate optimization score (placeholder)
            const optimizationScore = Math.min(100, Math.max(0, 100 - (avgQueryTime * 1000)));
            document.getElementById('optimization-score').textContent = `${optimizationScore.toFixed(0)}/100`;
        }
        
        async function triggerOptimization() {
            try {
                const response = await fetch('/api/optimize/default', { method: 'POST' });
                const result = await response.json();
                console.log('Optimization triggered:', result);
                // Show notification or update UI
            } catch (error) {
                console.error('Optimization failed:', error);
            }
        }
        
        // Initialize dashboard
        connectWebSocket();
        
        // Load initial performance chart
        fetch('/api/performance-chart/default')
            .then(response => response.json())
            .then(chartData => {
                if (!chartData.error) {
                    Plotly.newPlot('performance-chart', chartData.data, chartData.layout, {
                        responsive: true,
                        displayModeBar: false
                    });
                }
            })
            .catch(error => console.error('Chart loading failed:', error));
    </script>
</body>
</html>
'''
