import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { AlertCircle, TrendingUp, Clock, Users } from 'lucide-react';
import api from '../../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalErrors: 0,
    activeGroups: 0,
    resolvedToday: 0,
    criticalErrors: 0
  });
  const [errorTrends, setErrorTrends] = useState([]);
  const [recentGroups, setRecentGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [groupsResponse] = await Promise.all([
        api.get('/errors/groups')
      ]);
      
      const groups = groupsResponse.data.groups || [];
      
      // Calculate stats
      const newStats = {
        totalErrors: groups.reduce((sum, group) => sum + (group.count || 0), 0),
        activeGroups: groups.filter(g => g.status !== 'resolved' && g.status !== 'ignored').length,
        resolvedToday: groups.filter(g => 
          g.status === 'resolved' && 
          g.resolved_at &&
          new Date(g.resolved_at) > new Date(Date.now() - 24*60*60*1000)
        ).length,
        criticalErrors: groups.filter(g => g.level === 'critical').length
      };
      
      setStats(newStats);
      setRecentGroups(groups.slice(0, 5));
      
      // Generate mock trend data (in real app, this would come from API)
      const trendData = Array.from({ length: 7 }, (_, i) => ({
        day: new Date(Date.now() - (6-i) * 24*60*60*1000).toLocaleDateString('en-US', { weekday: 'short' }),
        errors: Math.floor(Math.random() * 100) + 20
      }));
      setErrorTrends(trendData);
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, trend, color = "blue" }) => (
    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold text-${color}-600 mt-1`}>{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600 ml-1">{trend}</span>
            </div>
          )}
        </div>
        <Icon className={`h-8 w-8 text-${color}-500`} />
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Error Tracking Dashboard</h1>
        <button 
          onClick={loadDashboardData}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Errors"
          value={stats.totalErrors}
          icon={AlertCircle}
          color="red"
        />
        <StatCard
          title="Active Groups"
          value={stats.activeGroups}
          icon={Users}
          color="orange"
        />
        <StatCard
          title="Resolved Today"
          value={stats.resolvedToday}
          icon={Clock}
          color="green"
        />
        <StatCard
          title="Critical Errors"
          value={stats.criticalErrors}
          icon={AlertCircle}
          color="red"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Error Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={errorTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="errors" stroke="#3B82F6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Error Groups</h3>
          <div className="space-y-3">
            {recentGroups.map(group => (
              <div key={group.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div>
                  <p className="font-medium text-gray-900 truncate max-w-xs">{group.title}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      group.status === 'new' ? 'bg-red-100 text-red-800' :
                      group.status === 'acknowledged' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {group.status}
                    </span>
                    <span className="text-sm text-gray-500">{group.count} occurrences</span>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  group.level === 'critical' ? 'bg-red-100 text-red-800' :
                  group.level === 'error' ? 'bg-orange-100 text-orange-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {group.level}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
