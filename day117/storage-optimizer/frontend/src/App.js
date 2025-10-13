import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Dashboard from './components/Dashboard';
import CostChart from './components/CostChart';
import PolicyManager from './components/PolicyManager';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [costData, setCostData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initial data load
    loadDashboardData();
    
    // Setup real-time updates
    const interval = setInterval(loadDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [metricsRes, costRes, historyRes] = await Promise.all([
        axios.get('http://localhost:8000/api/cost/realtime'),
        axios.get('http://localhost:8000/api/cost/tiers'),
        axios.get('http://localhost:8000/api/cost/history/7')
      ]);
      
      setMetrics(metricsRes.data);
      setCostData(historyRes.data);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to load data:', error);
      setIsLoading(false);
    }
  };

  const triggerOptimization = async () => {
    try {
      await axios.post('http://localhost:8000/api/optimize');
      loadDashboardData(); // Refresh data
    } catch (error) {
      console.error('Optimization failed:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="loading">
        <h2>Loading Storage Optimization Dashboard...</h2>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="app-header">
        <h1>🗂️ Storage Optimization Dashboard</h1>
        <button className="optimize-btn" onClick={triggerOptimization}>
          Run Optimization
        </button>
      </header>
      
      <main className="dashboard-container">
        <Dashboard metrics={metrics} />
        <div className="chart-section">
          <CostChart data={costData} />
        </div>
        <PolicyManager />
      </main>
    </div>
  );
}

export default App;
