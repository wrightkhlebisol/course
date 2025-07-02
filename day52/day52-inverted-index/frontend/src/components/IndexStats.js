import React from 'react';
import { Database, TrendingUp, Clock, Activity } from 'lucide-react';

const IndexStats = ({ stats }) => {
  if (!stats) {
    return (
      <div className="stats-container">
        <div className="stats-loading">Loading statistics...</div>
      </div>
    );
  }

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatLastUpdate = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  return (
    <div className="stats-container">
      <h2 className="stats-title">
        <Activity className="title-icon" size={24} />
        Index Statistics
      </h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <Database size={32} />
          </div>
          <div className="stat-content">
            <div className="stat-value">{formatNumber(stats.total_documents)}</div>
            <div className="stat-label">Documents Indexed</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <TrendingUp size={32} />
          </div>
          <div className="stat-content">
            <div className="stat-value">{formatNumber(stats.total_terms)}</div>
            <div className="stat-label">Unique Terms</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <Clock size={32} />
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.index_size_mb}MB</div>
            <div className="stat-label">Index Size</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <Activity size={32} />
          </div>
          <div className="stat-content">
            <div className="stat-value">{formatLastUpdate(stats.last_update)}</div>
            <div className="stat-label">Last Update</div>
          </div>
        </div>
      </div>
      
      {stats.most_frequent_terms && (
        <div className="frequent-terms">
          <h3>Most Frequent Terms</h3>
          <div className="terms-list">
            {stats.most_frequent_terms.slice(0, 5).map(([term, count], index) => (
              <div key={index} className="term-item">
                <span className="term">{term}</span>
                <span className="count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default IndexStats;
