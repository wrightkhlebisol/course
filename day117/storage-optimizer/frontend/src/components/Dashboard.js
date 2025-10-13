import React from 'react';

function Dashboard({ metrics }) {
  if (!metrics) return <div>Loading metrics...</div>;

  return (
    <div className="dashboard">
      <div className="metrics-grid">
        <div className="metric-card primary">
          <h3>Monthly Cost</h3>
          <div className="metric-value">${metrics.current_monthly_cost}</div>
          <div className="metric-change positive">
            ↓ ${metrics.potential_monthly_savings} saved
          </div>
        </div>
        
        <div className="metric-card">
          <h3>Savings</h3>
          <div className="metric-value">{metrics.savings_percentage}%</div>
          <div className="metric-subtitle">Cost Reduction</div>
        </div>
        
        <div className="metric-card">
          <h3>Optimization Score</h3>
          <div className="metric-value">{metrics.optimization_score}%</div>
          <div className="metric-subtitle">System Efficiency</div>
        </div>
        
        <div className="metric-card">
          <h3>Compression Ratio</h3>
          <div className="metric-value">{metrics.compression_ratio}:1</div>
          <div className="metric-subtitle">Space Savings</div>
        </div>
        
        <div className="metric-card">
          <h3>Storage Efficiency</h3>
          <div className="metric-value">{metrics.storage_efficiency}%</div>
          <div className="metric-subtitle">Optimal Placement</div>
        </div>
        
        <div className="metric-card">
          <h3>Active Optimizations</h3>
          <div className="metric-value">{metrics.active_optimizations}</div>
          <div className="metric-subtitle">Running Now</div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
