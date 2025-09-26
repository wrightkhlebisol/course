import React from 'react';

const StatsPanel = ({ stats }) => {
  const { cache, archives, active_jobs } = stats;

  const refreshIndex = async () => {
    try {
      const response = await fetch('/api/refresh-index', { method: 'POST' });
      if (response.ok) {
        alert('Archive index refreshed successfully!');
        window.location.reload();
      }
    } catch (error) {
      alert('Failed to refresh index: ' + error.message);
    }
  };

  const clearCache = async () => {
    try {
      const response = await fetch('/api/cache', { method: 'DELETE' });
      if (response.ok) {
        alert('Cache cleared successfully!');
        window.location.reload();
      }
    } catch (error) {
      alert('Failed to clear cache: ' + error.message);
    }
  };

  return (
    <div className="stats-panel">
      <h2>📊 System Statistics</h2>
      
      <div className="stats-grid">
        <div className="stats-card">
          <h3>💾 Cache Performance</h3>
          <div className="stats-content">
            <div className="stat-item">
              <span className="stat-label">Hit Rate:</span>
              <span className="stat-value">{(cache.hit_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Total Entries:</span>
              <span className="stat-value">{cache.total_entries}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Cache Hits:</span>
              <span className="stat-value">{cache.hits}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Cache Misses:</span>
              <span className="stat-value">{cache.misses}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Evictions:</span>
              <span className="stat-value">{cache.evictions}</span>
            </div>
          </div>
          <button onClick={clearCache} className="action-button">
            🗑️ Clear Cache
          </button>
        </div>

        <div className="stats-card">
          <h3>🗄️ Archive Information</h3>
          <div className="stats-content">
            <div className="stat-item">
              <span className="stat-label">Total Archives:</span>
              <span className="stat-value">{archives.total}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Last Scan:</span>
              <span className="stat-value">
                {archives.last_scan ? new Date(archives.last_scan).toLocaleString() : 'Never'}
              </span>
            </div>
          </div>
          <button onClick={refreshIndex} className="action-button">
            🔄 Refresh Index
          </button>
        </div>

        <div className="stats-card">
          <h3>⚡ Active Jobs</h3>
          <div className="stats-content">
            <div className="stat-item">
              <span className="stat-label">Running Jobs:</span>
              <span className="stat-value">{active_jobs}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;
