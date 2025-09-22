import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { Database, HardDrive, Archive, Trash2, TrendingDown, Shield } from 'lucide-react';

const Dashboard = () => {
  const [tierStats, setTierStats] = useState({});
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [tierResponse, policiesResponse] = await Promise.all([
        fetch('/api/tier-stats'),
        fetch('/api/policies')
      ]);
      
      const tierData = await tierResponse.json();
      const policiesData = await policiesResponse.json();
      
      setTierStats(tierData);
      setPolicies(policiesData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const getTierIcon = (tier) => {
    const icons = {
      hot: <Database className="w-6 h-6 text-red-500" />,
      warm: <HardDrive className="w-6 h-6 text-orange-500" />,
      cold: <Archive className="w-6 h-6 text-blue-500" />,
      archive: <Archive className="w-6 h-6 text-gray-500" />
    };
    return icons[tier] || <Database className="w-6 h-6" />;
  };

  const tierColors = {
    hot: '#ef4444',
    warm: '#f97316',
    cold: '#3b82f6',
    archive: '#6b7280'
  };

  const chartData = Object.entries(tierStats).map(([tier, stats]) => ({
    name: tier.toUpperCase(),
    files: stats.file_count,
    size: stats.size_gb,
    cost: stats.monthly_cost,
    utilization: stats.utilization_percent
  }));

  const totalCost = Object.values(tierStats).reduce((sum, stats) => sum + stats.monthly_cost, 0);
  const totalFiles = Object.values(tierStats).reduce((sum, stats) => sum + stats.file_count, 0);
  const totalSize = Object.values(tierStats).reduce((sum, stats) => sum + stats.size_gb, 0);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Data Lifecycle Management Dashboard</h1>
        <p>Real-time monitoring of policy-based data management</p>
      </header>

      {/* Summary Cards */}
      <div className="summary-grid">
        <div className="summary-card">
          <div className="card-icon">
            <Database className="w-8 h-8 text-blue-500" />
          </div>
          <div className="card-content">
            <h3>Total Files</h3>
            <p className="card-value">{totalFiles.toLocaleString()}</p>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">
            <HardDrive className="w-8 h-8 text-green-500" />
          </div>
          <div className="card-content">
            <h3>Total Storage</h3>
            <p className="card-value">{totalSize.toFixed(2)} GB</p>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">
            <TrendingDown className="w-8 h-8 text-orange-500" />
          </div>
          <div className="card-content">
            <h3>Monthly Cost</h3>
            <p className="card-value">${totalCost.toFixed(2)}</p>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">
            <Shield className="w-8 h-8 text-purple-500" />
          </div>
          <div className="card-content">
            <h3>Active Policies</h3>
            <p className="card-value">{policies.filter(p => p.enabled).length}</p>
          </div>
        </div>
      </div>

      {/* Storage Tier Breakdown */}
      <div className="charts-grid">
        <div className="chart-container">
          <h3>Storage Distribution by Tier</h3>
          <BarChart width={500} height={300} data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="files" fill="#8884d8" name="File Count" />
            <Bar dataKey="size" fill="#82ca9d" name="Size (GB)" />
          </BarChart>
        </div>

        <div className="chart-container">
          <h3>Cost Distribution</h3>
          <PieChart width={500} height={300}>
            <Pie
              data={chartData}
              cx={250}
              cy={150}
              outerRadius={80}
              fill="#8884d8"
              dataKey="cost"
              label={({name, value}) => `${name}: $${value.toFixed(2)}`}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={tierColors[entry.name.toLowerCase()]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </div>
      </div>

      {/* Tier Details */}
      <div className="tier-details">
        <h3>Storage Tier Details</h3>
        <div className="tier-grid">
          {Object.entries(tierStats).map(([tier, stats]) => (
            <div key={tier} className="tier-card">
              <div className="tier-header">
                {getTierIcon(tier)}
                <h4>{tier.toUpperCase()} Tier</h4>
              </div>
              <div className="tier-stats">
                <div className="stat">
                  <span className="stat-label">Files:</span>
                  <span className="stat-value">{stats.file_count}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Size:</span>
                  <span className="stat-value">{stats.size_gb.toFixed(2)} GB</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Cost:</span>
                  <span className="stat-value">${stats.monthly_cost.toFixed(2)}/mo</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Utilization:</span>
                  <span className="stat-value">{stats.utilization_percent}%</span>
                </div>
              </div>
              <div className="utilization-bar">
                <div 
                  className="utilization-fill"
                  style={{
                    width: `${Math.min(stats.utilization_percent, 100)}%`,
                    backgroundColor: tierColors[tier]
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
