import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Policies from './components/Policies';
import Jobs from './components/Jobs';
import Compliance from './components/Compliance';
import LogViewer from './components/LogViewer';
import Navigation from './components/Navigation';
import './styles/App.css';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/retention/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading retention dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard metrics={metrics} onMetricsRefresh={fetchMetrics} />} />
            <Route path="/policies" element={<Policies />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/logs" element={<LogViewer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 