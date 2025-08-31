import React, { useState, useEffect } from 'react';
import SystemDashboard from './components/SystemDashboard';
import LogSubmitter from './components/LogSubmitter';
import LoadTester from './components/LoadTester';
import SystemStatus from './components/SystemStatus';
import './styles/App.css';

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch initial system status
    fetchSystemStatus();
    
    // Set up polling for real-time updates
    const interval = setInterval(fetchSystemStatus, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/status');
      const data = await response.json();
      
      // Handle different response types
      if (response.status === 429) {
        // System under load - set the 429 response as status
        setSystemStatus(data);
      } else if (response.ok) {
        // Normal response
        setSystemStatus(data);
      } else {
        // Other error responses
        setSystemStatus({ error: 'API Error', message: `HTTP ${response.status}` });
      }
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      setSystemStatus({ error: 'Network Error', message: 'Failed to connect to backend' });
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading Backpressure System...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Distributed Log Processing System</h1>
          <h2>Day 62: Backpressure Mechanisms</h2>
          <div className="module-info">
            Module 2: Scalable Log Processing | Week 9: High Availability and Fault Tolerance
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="dashboard-grid">
          <div className="dashboard-section">
            <SystemStatus status={systemStatus} />
          </div>
          
          <div className="dashboard-section">
            <SystemDashboard status={systemStatus} />
          </div>
          
          <div className="dashboard-section">
            <LogSubmitter onSubmit={fetchSystemStatus} />
          </div>
          
          <div className="dashboard-section">
            <LoadTester onTestStart={fetchSystemStatus} />
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>254-Day Hands-On System Design with Distributed Log Processing System Implementation</p>
      </footer>
    </div>
  );
}

export default App;
