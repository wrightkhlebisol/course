import React, { useState, useEffect } from 'react';
import SearchInterface from './components/SearchInterface';
import IndexStats from './components/IndexStats';
import './styles/App.css';

function App() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1><span className="logo">🔍</span>Log Search System</h1>
          <p className="subtitle">Lightning-fast log search with inverted indexing</p>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          <div className="search-section">
            <SearchInterface />
          </div>
          
          <div className="stats-section">
            {loading ? (
              <div className="loading">Loading index statistics...</div>
            ) : (
              <IndexStats stats={stats} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
