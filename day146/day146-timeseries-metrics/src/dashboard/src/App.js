import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [responseTimeData, setResponseTimeData] = useState([]);
  const [errorRateData, setErrorRateData] = useState([]);
  const [resourceData, setResourceData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [responseTime, errorRate, resource, summaryData] = await Promise.all([
        axios.get(`${API_BASE_URL}/metrics/response-time?interval=1m`),
        axios.get(`${API_BASE_URL}/metrics/error-rate?interval=1m`),
        axios.get(`${API_BASE_URL}/metrics/resource-usage`),
        axios.get(`${API_BASE_URL}/metrics/summary`)
      ]);

      setResponseTimeData(responseTime.data.data.reverse().map(item => ({
        time: new Date(item.bucket).toLocaleTimeString(),
        avg: parseFloat(item.avg_response_time).toFixed(2),
        p95: parseFloat(item.p95_response_time).toFixed(2),
        service: item.service
      })));

      setErrorRateData(errorRate.data.data.reverse().map(item => ({
        time: new Date(item.bucket).toLocaleTimeString(),
        errorRate: parseFloat(item.error_rate).toFixed(2),
        totalRequests: item.total_requests,
        service: item.service
      })));

      setResourceData(resource.data.data.reverse().map(item => ({
        time: new Date(item.bucket).toLocaleTimeString(),
        cpu: parseFloat(item.avg_cpu).toFixed(2),
        memory: parseFloat(item.avg_memory).toFixed(2),
        service: item.service
      })));

      setSummary(summaryData.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading">Loading metrics dashboard...</div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎯 Time Series Metrics Dashboard</h1>
        <p>Real-time monitoring of distributed log processing system</p>
      </header>

      <div className="dashboard-grid">
        {/* Summary Cards */}
        <div className="summary-section">
          <h2>📊 System Summary (Last Hour)</h2>
          <div className="card-grid">
            {summary?.response_time?.map((item, idx) => (
              <div key={idx} className="metric-card">
                <h3>{item.service}</h3>
                <div className="metric-value">{parseFloat(item.avg_response_time).toFixed(2)}ms</div>
                <div className="metric-label">Avg Response Time</div>
                <div className="metric-secondary">
                  P95: {parseFloat(item.p95_response_time).toFixed(2)}ms
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Response Time Chart */}
        <div className="chart-section">
          <h2>⚡ Response Time Metrics</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={responseTimeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
              <XAxis dataKey="time" stroke="#a0a0a0" tick={{ fill: '#a0a0a0' }} />
              <YAxis stroke="#a0a0a0" tick={{ fill: '#a0a0a0' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1a1f3a', 
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: '#e0e0e0'
                }} 
              />
              <Legend wrapperStyle={{ color: '#e0e0e0' }} />
              <Line type="monotone" dataKey="avg" stroke="#00d4aa" strokeWidth={2.5} name="Average" dot={false} />
              <Line type="monotone" dataKey="p95" stroke="#ff9500" strokeWidth={2.5} name="P95" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Error Rate Chart */}
        <div className="chart-section">
          <h2>🚨 Error Rate</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={errorRateData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
              <XAxis dataKey="time" stroke="#a0a0a0" tick={{ fill: '#a0a0a0' }} />
              <YAxis stroke="#a0a0a0" tick={{ fill: '#a0a0a0' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1a1f3a', 
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: '#e0e0e0'
                }} 
              />
              <Legend wrapperStyle={{ color: '#e0e0e0' }} />
              <Bar dataKey="errorRate" fill="#ff4444" name="Error Rate (%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Resource Usage Chart */}
        <div className="chart-section">
          <h2>💻 Resource Usage</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={resourceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" />
              <XAxis dataKey="time" stroke="#a0a0a0" tick={{ fill: '#a0a0a0' }} />
              <YAxis stroke="#a0a0a0" tick={{ fill: '#a0a0a0' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1a1f3a', 
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: '#e0e0e0'
                }} 
              />
              <Legend wrapperStyle={{ color: '#e0e0e0' }} />
              <Line type="monotone" dataKey="cpu" stroke="#ffaa00" strokeWidth={2.5} name="CPU %" dot={false} />
              <Line type="monotone" dataKey="memory" stroke="#00d4aa" strokeWidth={2.5} name="Memory MB" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <footer className="App-footer">
        <p>Last updated: {new Date().toLocaleTimeString()}</p>
        <p>Powered by TimescaleDB + FastAPI + React</p>
      </footer>
    </div>
  );
}

export default App;
