import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

function DashboardPage({ user, onLogout }) {
    const [stats, setStats] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [logs, setLogs] = useState([]);
    const [searchFilters, setSearchFilters] = useState({
        level: '',
        service: '',
        limit: 50
    });
    const [loading, setLoading] = useState(true);

    const getAuthHeaders = () => ({
        Authorization: `Bearer ${localStorage.getItem('authToken')}`
    });

    const fetchStats = async () => {
        try {
            const response = await axios.get('/api/v1/tenants/me/stats', {
                headers: getAuthHeaders()
            });
            setStats(response.data);
        } catch (error) {
            console.error('Failed to fetch stats:', error);
        }
    };

    const fetchAnalytics = async () => {
        try {
            const response = await axios.get('/api/v1/logs/analytics', {
                headers: getAuthHeaders()
            });
            setAnalytics(response.data);
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        }
    };

    const searchLogs = async () => {
        try {
            const response = await axios.post('/api/v1/logs/search', searchFilters, {
                headers: getAuthHeaders()
            });
            setLogs(response.data.logs);
        } catch (error) {
            console.error('Failed to search logs:', error);
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            await Promise.all([fetchStats(), fetchAnalytics(), searchLogs()]);
            setLoading(false);
        };
        fetchData();
    }, []);

    useEffect(() => {
        searchLogs();
    }, [searchFilters]);

    const levelChartData = analytics ? {
        labels: Object.keys(analytics.level_distribution),
        datasets: [{
            data: Object.values(analytics.level_distribution),
            backgroundColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF'
            ]
        }]
    } : { labels: [], datasets: [] };

    const activityChartData = analytics ? {
        labels: analytics.hourly_activity.map(item => 
            new Date(item.hour).toLocaleTimeString()
        ),
        datasets: [{
            label: 'Log Count',
            data: analytics.hourly_activity.map(item => item.count),
            backgroundColor: '#36A2EB'
        }]
    } : { labels: [], datasets: [] };

    if (loading) {
        return <div className="loading">Loading dashboard...</div>;
    }

    return (
        <div className="dashboard">
            <header className="header">
                <h1>Multi-Tenant Log Platform</h1>
                <div className="user-info">
                    <span>Welcome, {user.username} ({user.tenant_domain})</span>
                    <button onClick={onLogout} className="logout-btn">
                        Logout
                    </button>
                </div>
            </header>

            <main className="main-content">
                {stats && (
                    <div className="stats-grid">
                        <div className="stat-card">
                            <h3>Total Logs</h3>
                            <div className="value">{stats.total_logs.toLocaleString()}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Total Users</h3>
                            <div className="value">{stats.total_users}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Service Tier</h3>
                            <div className="value">{stats.service_tier}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Status</h3>
                            <div className="value">{stats.status}</div>
                        </div>
                    </div>
                )}

                {analytics && (
                    <>
                        <div className="chart-section">
                            <h2>Log Level Distribution</h2>
                            <div style={{ height: '300px', display: 'flex', justifyContent: 'center' }}>
                                <Doughnut 
                                    data={levelChartData} 
                                    options={{ maintainAspectRatio: false }}
                                />
                            </div>
                        </div>

                        <div className="chart-section">
                            <h2>Activity (Last 24 Hours)</h2>
                            <Bar 
                                data={activityChartData}
                                options={{
                                    responsive: true,
                                    plugins: {
                                        legend: { display: false }
                                    }
                                }}
                            />
                        </div>
                    </>
                )}

                <div className="log-search">
                    <h2>Recent Logs</h2>
                    
                    <div className="search-filters">
                        <div className="form-group">
                            <label>Level</label>
                            <select
                                value={searchFilters.level}
                                onChange={(e) => setSearchFilters({
                                    ...searchFilters,
                                    level: e.target.value
                                })}
                            >
                                <option value="">All Levels</option>
                                <option value="ERROR">Error</option>
                                <option value="WARNING">Warning</option>
                                <option value="INFO">Info</option>
                                <option value="DEBUG">Debug</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Service</label>
                            <input
                                type="text"
                                value={searchFilters.service}
                                onChange={(e) => setSearchFilters({
                                    ...searchFilters,
                                    service: e.target.value
                                })}
                                placeholder="Filter by service"
                            />
                        </div>

                        <div className="form-group">
                            <label>Limit</label>
                            <select
                                value={searchFilters.limit}
                                onChange={(e) => setSearchFilters({
                                    ...searchFilters,
                                    limit: parseInt(e.target.value)
                                })}
                            >
                                <option value={10}>10</option>
                                <option value={50}>50</option>
                                <option value={100}>100</option>
                            </select>
                        </div>
                    </div>

                    <div className="log-entries">
                        {logs.map((log) => (
                            <div key={log.id} className="log-entry">
                                <div className="header-row">
                                    <span className={`log-level ${log.level.toLowerCase()}`}>
                                        {log.level}
                                    </span>
                                    <span>{new Date(log.timestamp).toLocaleString()}</span>
                                </div>
                                <div className="log-message">{log.message}</div>
                                <div className="log-meta">
                                    Source: {log.source || 'Unknown'} | 
                                    Service: {log.service || 'Unknown'}
                                </div>
                            </div>
                        ))}
                        
                        {logs.length === 0 && (
                            <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
                                No logs found for the current filters.
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}

export default DashboardPage;
