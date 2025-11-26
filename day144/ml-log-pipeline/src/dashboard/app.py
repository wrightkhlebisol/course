"""React-based monitoring dashboard"""
import json
from pathlib import Path

# Create React dashboard
dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ML Log Pipeline Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        :root {
            --primary-color: #2563eb;
            --primary-dark: #1e40af;
            --primary-light: #3b82f6;
            --success-color: #10b981;
            --success-light: #d1fae5;
            --danger-color: #ef4444;
            --danger-light: #fee2e2;
            --warning-color: #f59e0b;
            --warning-light: #fef3c7;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --text-tertiary: #9ca3af;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --border-color: #e5e7eb;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 24px;
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        .container {
            max-width: 1440px;
            margin: 0 auto;
        }
        
        .header {
            background: var(--bg-primary);
            padding: 32px 40px;
            border-radius: 12px;
            box-shadow: var(--shadow-lg);
            margin-bottom: 32px;
            border: 1px solid var(--border-color);
        }
        
        .header h1 {
            color: var(--text-primary);
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 15px;
            font-weight: 400;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
        }
        
        .card {
            background: var(--bg-primary);
            padding: 28px;
            border-radius: 12px;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }
        
        .card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        
        .card h2 {
            color: var(--text-primary);
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--bg-tertiary);
            letter-spacing: -0.3px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: var(--bg-secondary);
            border-radius: 8px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }
        
        .metric:hover {
            background: var(--bg-tertiary);
            border-color: var(--border-color);
        }
        
        .metric-label {
            font-weight: 500;
            color: var(--text-secondary);
            font-size: 14px;
            letter-spacing: 0.01em;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary-color);
            letter-spacing: -0.5px;
        }
        
        .prediction-item {
            padding: 20px;
            background: var(--bg-secondary);
            border-left: 4px solid var(--primary-color);
            border-radius: 8px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
            border-top: 1px solid var(--border-color);
            border-right: 1px solid var(--border-color);
            border-bottom: 1px solid var(--border-color);
        }
        
        .prediction-item:hover {
            background: var(--bg-tertiary);
            box-shadow: var(--shadow-sm);
        }
        
        .anomaly {
            border-left-color: var(--danger-color);
            background: var(--danger-light);
        }
        
        .anomaly:hover {
            background: #fecaca;
        }
        
        .normal {
            border-left-color: var(--success-color);
            background: var(--success-light);
        }
        
        .normal:hover {
            background: #a7f3d0;
        }
        
        .prediction-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .confidence-bar {
            height: 6px;
            background: var(--bg-tertiary);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 12px;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-light) 100%);
            transition: width 0.5s ease;
            border-radius: 3px;
        }
        
        .button {
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: inherit;
            letter-spacing: 0.01em;
            box-shadow: var(--shadow-sm);
        }
        
        .button:hover:not(:disabled) {
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .button:active:not(:disabled) {
            transform: translateY(0);
        }
        
        .button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
        }
        
        .status-healthy { 
            background: var(--success-color);
            box-shadow: 0 0 0 2px var(--success-light);
        }
        
        .status-warning { 
            background: var(--warning-color);
            box-shadow: 0 0 0 2px var(--warning-light);
        }
        
        .status-critical { 
            background: var(--danger-color);
            box-shadow: 0 0 0 2px var(--danger-light);
        }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect } = React;
        
        function Dashboard() {
            const [stats, setStats] = useState({
                totalPredictions: 0,
                anomaliesDetected: 0,
                avgConfidence: 0,
                modelsHealthy: true
            });
            const [predictions, setPredictions] = useState([]);
            const [loading, setLoading] = useState(false);
            
            useEffect(() => {
                fetchMetrics();
                const interval = setInterval(fetchMetrics, 5000);
                return () => clearInterval(interval);
            }, []);
            
            const fetchMetrics = async () => {
                try {
                    const response = await fetch('http://localhost:8000/metrics');
                    const data = await response.json();
                    // Update stats based on API response
                } catch (error) {
                    console.error('Error fetching metrics:', error);
                }
            };
            
            const generateTestPrediction = () => {
                setLoading(true);
                setTimeout(() => {
                    const isAnomaly = Math.random() > 0.7;
                    const newPrediction = {
                        id: Date.now(),
                        timestamp: new Date().toISOString(),
                        isAnomaly,
                        confidence: (Math.random() * 0.4 + 0.6).toFixed(3),
                        service: ['web', 'api', 'database'][Math.floor(Math.random() * 3)],
                        level: isAnomaly ? 'ERROR' : 'INFO'
                    };
                    
                    setPredictions(prev => [newPrediction, ...prev].slice(0, 10));
                    setStats(prev => ({
                        ...prev,
                        totalPredictions: prev.totalPredictions + 1,
                        anomaliesDetected: prev.anomaliesDetected + (isAnomaly ? 1 : 0)
                    }));
                    setLoading(false);
                }, 500);
            };
            
            return (
                <div className="container">
                    <div className="header">
                        <h1>🤖 ML Log Pipeline Dashboard</h1>
                        <p>Real-time anomaly detection and failure prediction</p>
                    </div>
                    
                    <div className="grid">
                        <div className="card">
                            <h2>📊 System Metrics</h2>
                            <div className="metric">
                                <span className="metric-label">Total Predictions</span>
                                <span className="metric-value">{stats.totalPredictions}</span>
                            </div>
                            <div className="metric">
                                <span className="metric-label">Anomalies Detected</span>
                                <span className="metric-value" style={{color: 'var(--danger-color)'}}>
                                    {stats.anomaliesDetected}
                                </span>
                            </div>
                            <div className="metric">
                                <span className="metric-label">Detection Rate</span>
                                <span className="metric-value">
                                    {stats.totalPredictions > 0 
                                        ? ((stats.anomaliesDetected / stats.totalPredictions) * 100).toFixed(1)
                                        : 0}%
                                </span>
                            </div>
                        </div>
                        
                        <div className="card">
                            <h2>🎯 Model Status</h2>
                            <div className="metric">
                                <span className="metric-label">
                                    <span className="status-indicator status-healthy"></span>
                                    Anomaly Detector
                                </span>
                                <span className="metric-value" style={{fontSize: '14px', color: 'var(--success-color)', fontWeight: '600'}}>
                                    READY
                                </span>
                            </div>
                            <div className="metric">
                                <span className="metric-label">
                                    <span className="status-indicator status-healthy"></span>
                                    Failure Predictor
                                </span>
                                <span className="metric-value" style={{fontSize: '14px', color: 'var(--success-color)', fontWeight: '600'}}>
                                    READY
                                </span>
                            </div>
                            <button 
                                className="button" 
                                onClick={generateTestPrediction}
                                disabled={loading}
                                style={{width: '100%', marginTop: '15px'}}
                            >
                                {loading ? '⏳ Processing...' : '🔮 Test Prediction'}
                            </button>
                        </div>
                    </div>
                    
                    <div className="card">
                        <h2>📈 Recent Predictions</h2>
                        {predictions.length === 0 ? (
                            <p style={{textAlign: 'center', color: 'var(--text-tertiary)', padding: '32px 20px', fontSize: '14px'}}>
                                No predictions yet. Click "Test Prediction" to generate one.
                            </p>
                        ) : (
                            predictions.map(pred => (
                                <div key={pred.id} className={`prediction-item ${pred.isAnomaly ? 'anomaly' : 'normal'}`}>
                                    <div className="prediction-header">
                                        <strong style={{color: pred.isAnomaly ? 'var(--danger-color)' : 'var(--success-color)', fontSize: '13px', fontWeight: '600', letterSpacing: '0.05em'}}>
                                            {pred.isAnomaly ? '⚠️ ANOMALY' : '✅ NORMAL'}
                                        </strong>
                                        <span style={{color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '500'}}>
                                            {new Date(pred.timestamp).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    <div style={{fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px', fontWeight: '400'}}>
                                        Service: <strong style={{color: 'var(--text-primary)'}}>{pred.service}</strong> | Level: <strong style={{color: 'var(--text-primary)'}}>{pred.level}</strong>
                                    </div>
                                    <div className="confidence-bar">
                                        <div 
                                            className="confidence-fill" 
                                            style={{width: `${pred.confidence * 100}%`}}
                                        ></div>
                                    </div>
                                    <div style={{fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '8px', fontWeight: '500'}}>
                                        Confidence: <strong style={{color: 'var(--text-secondary)'}}>{(pred.confidence * 100).toFixed(1)}%</strong>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            );
        }
        
        ReactDOM.render(<Dashboard />, document.getElementById('root'));
    </script>
</body>
</html>
'''

# Save dashboard
Path("src/dashboard/static").mkdir(parents=True, exist_ok=True)
with open("src/dashboard/static/index.html", "w") as f:
    f.write(dashboard_html)
