import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { Activity, Flag, Users, TrendingUp } from 'lucide-react';
import api from '../services/api';

const StatCard = ({ title, value, icon: Icon, change, color = "blue" }) => {
  const colorClasses = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-green-600 bg-green-50",
    yellow: "text-yellow-600 bg-yellow-50",
    red: "text-red-600 bg-red-50"
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '+' : ''}{change}% from last hour
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalFlags: 0,
    activeFlags: 0,
    totalEvaluations: 0,
    recentChanges: 0
  });

  const { data: flags = [] } = useQuery('flags', api.getFlags);
  const { data: recentLogs = [] } = useQuery('recentLogs', api.getRecentLogs, {
    refetchInterval: 5000
  });

  useEffect(() => {
    if (flags.length > 0) {
      setStats({
        totalFlags: flags.length,
        activeFlags: flags.filter(f => f.enabled).length,
        totalEvaluations: recentLogs.filter(l => l.event_type === 'evaluate').length,
        recentChanges: recentLogs.filter(l => l.event_type === 'update').length
      });
    }
  }, [flags, recentLogs]);

  // Prepare chart data
  const flagStatusData = [
    { name: 'Enabled', value: stats.activeFlags, color: '#10b981' },
    { name: 'Disabled', value: stats.totalFlags - stats.activeFlags, color: '#ef4444' }
  ];

  const activityData = recentLogs.slice(0, 10).map((log, index) => ({
    name: `${log.event_type}`,
    value: index + 1,
    time: new Date(log.timestamp).toLocaleTimeString()
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Feature Flag Dashboard</h1>
        <p className="text-gray-600">Monitor your feature flags and their activity in real-time</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Flags"
          value={stats.totalFlags}
          icon={Flag}
          change={5}
          color="blue"
        />
        <StatCard
          title="Active Flags"
          value={stats.activeFlags}
          icon={Activity}
          change={2}
          color="green"
        />
        <StatCard
          title="Evaluations (1h)"
          value={stats.totalEvaluations}
          icon={TrendingUp}
          change={12}
          color="yellow"
        />
        <StatCard
          title="Recent Changes"
          value={stats.recentChanges}
          icon={Users}
          change={-1}
          color="red"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Flag Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={flagStatusData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="value"
                label={({name, value}) => `${name}: ${value}`}
              >
                {flagStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Recent Flag Activity</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Flag Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentLogs.slice(0, 5).map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {log.flag_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      log.event_type === 'create' ? 'bg-green-100 text-green-800' :
                      log.event_type === 'update' ? 'bg-blue-100 text-blue-800' :
                      log.event_type === 'delete' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.user_id || 'System'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
