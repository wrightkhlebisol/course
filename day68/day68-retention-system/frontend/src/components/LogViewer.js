import React, { useState, useEffect } from 'react';
import { FileText, Search, Filter, Download, RefreshCw } from 'lucide-react';

const LogViewer = () => {
  const [logStats, setLogStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    storage_type: '',
    log_type: '',
    level: ''
  });

  const storageTypes = ['hot', 'warm', 'cold'];
  const logTypes = ['application', 'security', 'system', 'error', 'access'];
  const logLevels = ['debug', 'info', 'warning', 'error', 'critical'];

  useEffect(() => {
    fetchLogStats();
  }, []);

  const fetchLogStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/logs/stats');
      const data = await response.json();
      setLogStats(data.stats);
    } catch (error) {
      console.error('Error fetching log stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateLogs = async () => {
    try {
      setLoading(true);
      await fetch('http://localhost:8000/api/logs/generate?count=100', { method: 'POST' });
      await fetchLogStats();
    } catch (error) {
      console.error('Error generating logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.storage_type) params.append('storage_type', filters.storage_type);
      if (filters.log_type) params.append('log_type', filters.log_type);
      if (filters.level) params.append('level', filters.level);
      params.append('limit', '50');

      const response = await fetch(`/api/logs/search?${params}`);
      const data = await response.json();
      setLogs(data.logs);
    } catch (error) {
      console.error('Error searching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const cleanupLogs = async () => {
    try {
      setLoading(true);
      await fetch('http://localhost:8000/api/logs/cleanup?days_to_keep=30', { method: 'POST' });
      await fetchLogStats();
      setLogs([]);
    } catch (error) {
      console.error('Error cleaning up logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getLevelColor = (level) => {
    const colors = {
      debug: 'text-gray-500',
      info: 'text-blue-600',
      warning: 'text-yellow-600',
      error: 'text-red-600',
      critical: 'text-red-800'
    };
    return colors[level] || 'text-gray-600';
  };

  const getTypeColor = (type) => {
    const colors = {
      application: 'bg-blue-100 text-blue-800',
      security: 'bg-red-100 text-red-800',
      system: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      access: 'bg-purple-100 text-purple-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Log Monitor</h1>
            <p className="text-gray-600">Monitor and manage log files across storage tiers</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={generateLogs}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <FileText className="h-4 w-4" />
              <span>Generate Logs</span>
            </button>
            <button
              onClick={fetchLogStats}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* Log Statistics */}
      {logStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Files</p>
                <p className="text-3xl font-bold text-blue-600">{logStats.total_files}</p>
              </div>
              <FileText className="h-12 w-12 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Size</p>
                <p className="text-3xl font-bold text-green-600">{logStats.total_size_mb.toFixed(2)} MB</p>
              </div>
              <Download className="h-12 w-12 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Recent Logs</p>
                <p className="text-3xl font-bold text-purple-600">{logStats.recent_logs.length}</p>
              </div>
              <Search className="h-12 w-12 text-purple-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Storage Tiers</p>
                <p className="text-3xl font-bold text-orange-600">{Object.keys(logStats.by_storage).length}</p>
              </div>
              <Filter className="h-12 w-12 text-orange-500" />
            </div>
          </div>
        </div>
      )}

      {/* Storage Breakdown */}
      {logStats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {Object.entries(logStats.by_storage).map(([storageType, stats]) => (
            <div key={storageType} className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 capitalize">{storageType} Storage</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Files:</span>
                  <span className="font-medium">{stats.files}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Size:</span>
                  <span className="font-medium">{stats.size_mb.toFixed(2)} MB</span>
                </div>
                <div className="border-t pt-3">
                  <p className="text-sm font-medium text-gray-700 mb-2">Log Types:</p>
                  <div className="space-y-1">
                    {Object.entries(stats.types).map(([type, count]) => (
                      <div key={type} className="flex justify-between text-xs">
                        <span className="capitalize">{type}:</span>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Search Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Search Logs</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Storage Type</label>
            <select
              value={filters.storage_type}
              onChange={(e) => setFilters({...filters, storage_type: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Storage Types</option>
              {storageTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Log Type</label>
            <select
              value={filters.log_type}
              onChange={(e) => setFilters({...filters, log_type: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Log Types</option>
              {logTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Log Level</label>
            <select
              value={filters.level}
              onChange={(e) => setFilters({...filters, level: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Levels</option>
              {logLevels.map(level => (
                <option key={level} value={level}>{level}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={searchLogs}
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <Search className="h-4 w-4" />
              <span>Search</span>
            </button>
          </div>
        </div>
      </div>

      {/* Log Results */}
      {logs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Search Results ({logs.length} logs)</h3>
            <button
              onClick={cleanupLogs}
              disabled={loading}
              className="flex items-center space-x-2 px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
            >
              <span>Cleanup Old Logs</span>
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Level</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Storage</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(log.type)}`}>
                        {log.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${getLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                      {log.message}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                      {log.storage_type}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading...</span>
        </div>
      )}
    </div>
  );
};

export default LogViewer; 