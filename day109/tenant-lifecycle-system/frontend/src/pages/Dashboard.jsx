import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import axios from 'axios'

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/stats/dashboard')
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">Loading dashboard...</div>

  const chartData = stats ? Object.entries(stats.state_distribution).map(([state, count]) => ({
    state: state.charAt(0).toUpperCase() + state.slice(1),
    count
  })) : []

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Tenant Lifecycle Dashboard</h1>
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Tenants</h3>
            <div className="stat-number">{stats?.total_tenants || 0}</div>
          </div>
          <div className="stat-card">
            <h3>Active</h3>
            <div className="stat-number success">{stats?.state_distribution?.active || 0}</div>
          </div>
          <div className="stat-card">
            <h3>Provisioning</h3>
            <div className="stat-number warning">{stats?.state_distribution?.provisioning || 0}</div>
          </div>
          <div className="stat-card">
            <h3>Deprovisioning</h3>
            <div className="stat-number error">{stats?.state_distribution?.deprovisioning || 0}</div>
          </div>
        </div>
      </div>

      <div className="charts-section">
        <div className="chart-container">
          <h3>Tenant State Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="state" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="recent-activity">
        <h3>Recent Activity</h3>
        <div className="activity-list">
          {stats?.recent_activity?.map((activity, index) => (
            <div key={index} className="activity-item">
              <span className="activity-time">{new Date(activity.timestamp).toLocaleString()}</span>
              <span className="activity-action">{activity.action.replace('_', ' ')}</span>
              <span className="activity-tenant">{activity.tenant_id}</span>
              <span className={`activity-status ${activity.status}`}>{activity.status}</span>
            </div>
          )) || <p>No recent activity</p>}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
