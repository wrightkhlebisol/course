import React, { useState, useEffect } from 'react';
import './App.css';
import QueryForm from './components/QueryForm';
import ResultsTable from './components/ResultsTable';
import StatsPanel from './components/StatsPanel';
import ArchivesList from './components/ArchivesList';

function App() {
  const [activeTab, setActiveTab] = useState('query');
  const [queryResults, setQueryResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleQuery = async (queryData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(queryData),
      });
      
      if (!response.ok) {
        throw new Error(`Query failed: ${response.statusText}`);
      }
      
      const results = await response.json();
      setQueryResults(results);
    } catch (error) {
      console.error('Query failed:', error);
      alert('Query failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🗄️ Archive Restoration System</h1>
        <p>Query historical log data from archives</p>
      </header>

      <nav className="nav-tabs">
        <button 
          className={activeTab === 'query' ? 'active' : ''} 
          onClick={() => setActiveTab('query')}
        >
          Query Data
        </button>
        <button 
          className={activeTab === 'archives' ? 'active' : ''} 
          onClick={() => setActiveTab('archives')}
        >
          Archives
        </button>
        <button 
          className={activeTab === 'stats' ? 'active' : ''} 
          onClick={() => setActiveTab('stats')}
        >
          Statistics
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'query' && (
          <div className="query-section">
            <QueryForm onQuery={handleQuery} loading={loading} />
            {queryResults && <ResultsTable results={queryResults} />}
          </div>
        )}

        {activeTab === 'archives' && (
          <ArchivesList />
        )}

        {activeTab === 'stats' && stats && (
          <StatsPanel stats={stats} />
        )}
      </main>
    </div>
  );
}

export default App;
