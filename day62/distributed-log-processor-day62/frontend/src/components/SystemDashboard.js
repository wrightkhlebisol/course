import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

const SystemDashboard = ({ status }) => {
  if (!status) return <div>Loading dashboard...</div>;

  // Handle 429 responses or incomplete status
  if (status.error || !status.backpressure) {
    return (
      <div className="system-dashboard">
        <h3>📊 Real-time System Metrics</h3>
        <div className="charts-container">
          <div className="chart-section">
            <h4>⚡ System Under Backpressure</h4>
            <div className="backpressure-message">
              <p>📈 The system is currently under high load and backpressure mechanisms are active.</p>
              <p>🔄 Dashboard will resume normal display when load decreases.</p>
              <p>⏱️ {status.message || 'Please wait for system recovery...'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { backpressure, processor, metrics } = status;

  // Mock time series data for demonstration
  const timeSeriesData = [
    { time: '10:00', pressure: 0.2, throttle: 1.0, queue: 100 },
    { time: '10:01', pressure: 0.3, throttle: 1.0, queue: 150 },
    { time: '10:02', pressure: 0.5, throttle: 0.9, queue: 300 },
    { time: '10:03', pressure: 0.7, throttle: 0.7, queue: 500 },
    { time: '10:04', pressure: 0.9, throttle: 0.3, queue: 800 },
    { time: '10:05', pressure: 0.6, throttle: 0.8, queue: 400 },
  ];

  const queueData = Object.entries(processor.queue_sizes || {}).map(([priority, size]) => ({
    priority,
    size,
    color: priority === 'CRITICAL' ? '#ea4335' : 
           priority === 'HIGH' ? '#fbbc04' :
           priority === 'NORMAL' ? '#34a853' : '#4285f4'
  }));

  return (
    <div className="system-dashboard">
      <h3>📊 Real-time System Metrics</h3>
      
      <div className="charts-container">
        <div className="chart-section">
          <h4>Pressure & Throttling Over Time</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="pressure" stroke="#ea4335" name="Pressure Score" />
              <Line type="monotone" dataKey="throttle" stroke="#34a853" name="Throttle Rate" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-section">
          <h4>Queue Sizes by Priority</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={queueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="priority" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="size" fill="#4285f4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="metrics-summary">
        <h4>Resource Utilization</h4>
        <div className="resource-meters">
          <div className="meter">
            <label>CPU Usage</label>
            <div className="meter-bar">
              <div 
                className="meter-fill"
                style={{ 
                  width: `${metrics.gauges?.cpu_percent || 0}%`,
                  backgroundColor: (metrics.gauges?.cpu_percent || 0) > 80 ? '#ea4335' : '#34a853'
                }}
              ></div>
            </div>
            <span>{(metrics.gauges?.cpu_percent || 0).toFixed(1)}%</span>
          </div>
          
          <div className="meter">
            <label>Memory Usage</label>
            <div className="meter-bar">
              <div 
                className="meter-fill"
                style={{ 
                  width: `${metrics.gauges?.memory_percent || 0}%`,
                  backgroundColor: (metrics.gauges?.memory_percent || 0) > 80 ? '#ea4335' : '#34a853'
                }}
              ></div>
            </div>
            <span>{(metrics.gauges?.memory_percent || 0).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemDashboard;
