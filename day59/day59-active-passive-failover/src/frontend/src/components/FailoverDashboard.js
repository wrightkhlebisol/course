import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, Server, AlertTriangle, CheckCircle } from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';
import './FailoverDashboard.css';

const FailoverDashboard = () => {
  const [nodes, setNodes] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [failoverEvents, setFailoverEvents] = useState([]);
  const [systemHealth, setSystemHealth] = useState('healthy');
  
  const { connected, sendMessage } = useWebSocket('ws://localhost:8001/ws');
  
  useEffect(() => {
    // Fetch initial data
    fetchNodeStatus();
    fetchMetrics();
    fetchFailoverEvents();
    
    // Set up polling
    const interval = setInterval(() => {
      fetchNodeStatus();
      fetchMetrics();
    }, 2000);
    
    return () => clearInterval(interval);
  }, []);
  
  const fetchNodeStatus = async () => {
    try {
      const response = await fetch('/api/nodes/status');
      const data = await response.json();
      setNodes(data.nodes || []);
      setSystemHealth(data.system_health || 'healthy');
    } catch (error) {
      console.error('Error fetching node status:', error);
    }
  };
  
  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/metrics');
      const data = await response.json();
      setMetrics(prev => [...prev.slice(-50), {
        timestamp: new Date().toLocaleTimeString(),
        throughput: data.throughput || 0,
        latency: data.latency || 0,
        activeNodes: data.active_nodes || 0
      }]);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };
  
  const fetchFailoverEvents = async () => {
    try {
      const response = await fetch('/api/failover/events');
      const data = await response.json();
      setFailoverEvents(data.events || []);
    } catch (error) {
      console.error('Error fetching failover events:', error);
    }
  };
  
  const triggerFailover = async (nodeId) => {
    try {
      await fetch(`/api/nodes/${nodeId}/trigger-failover`, {
        method: 'POST'
      });
      fetchNodeStatus();
    } catch (error) {
      console.error('Error triggering failover:', error);
    }
  };
  
  const getNodeStatusIcon = (status) => {
    switch (status) {
      case 'primary':
        return <CheckCircle className="status-icon primary" />;
      case 'standby':
        return <Server className="status-icon standby" />;
      case 'failed':
        return <AlertTriangle className="status-icon failed" />;
      default:
        return <Activity className="status-icon inactive" />;
    }
  };
  
  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy':
        return '#10b981';
      case 'degraded':
        return '#f59e0b';
      case 'unhealthy':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };
  
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="system-status">
          <div className="status-indicator" style={{ backgroundColor: getHealthColor(systemHealth) }}></div>
          <span className="system-health">System Health: {systemHealth}</span>
        </div>
        <div className="connection-status">
          <span className={`connection-indicator ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
      
      <div className="dashboard-grid">
        <div className="card nodes-card">
          <h3>Node Status</h3>
          <div className="nodes-grid">
            {nodes.map(node => (
              <div key={node.id} className={`node-card ${node.status}`}>
                <div className="node-header">
                  {getNodeStatusIcon(node.status)}
                  <h4>{node.id}</h4>
                </div>
                <div className="node-details">
                  <p><strong>Role:</strong> {node.role}</p>
                  <p><strong>Status:</strong> {node.status}</p>
                  <p><strong>Port:</strong> {node.port}</p>
                  <p><strong>Uptime:</strong> {node.uptime}s</p>
                </div>
                <div className="node-metrics">
                  <div className="metric">
                    <span className="metric-label">Processed:</span>
                    <span className="metric-value">{node.processed_logs}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Queries:</span>
                    <span className="metric-value">{node.search_queries}</span>
                  </div>
                </div>
                {node.status === 'primary' && (
                  <button 
                    className="failover-btn"
                    onClick={() => triggerFailover(node.id)}
                  >
                    Trigger Failover
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
        
        <div className="card metrics-card">
          <h3>System Metrics</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="throughput" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="Throughput (logs/sec)"
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="latency" 
                stroke="#ef4444" 
                strokeWidth={2}
                name="Latency (ms)"
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="activeNodes" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Active Nodes"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="card events-card">
          <h3>Failover Events</h3>
          <div className="events-list">
            {failoverEvents.map((event, index) => (
              <div key={index} className="event-item">
                <div className="event-timestamp">
                  {new Date(event.timestamp * 1000).toLocaleString()}
                </div>
                <div className="event-details">
                  <strong>{event.type}</strong>
                  <p>{event.details}</p>
                  <span className="event-node">Node: {event.node_id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FailoverDashboard;
