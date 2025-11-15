import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, Clock, Filter } from 'lucide-react';
import api from '../../services/api';

const ErrorList = () => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    level: '',
    platform: ''
  });

  useEffect(() => {
    loadErrorGroups();
  }, [filters]);

  const loadErrorGroups = async () => {
    setLoading(true);
    try {
      const params = Object.entries(filters)
        .filter(([key, value]) => value)
        .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});
      
      const response = await api.get('/errors/groups', { params });
      setGroups(response.data.groups || []);
    } catch (error) {
      console.error('Failed to load error groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateGroupStatus = async (groupId, status) => {
    try {
      await api.put(`/errors/groups/${groupId}/status`, { status });
      loadErrorGroups(); // Reload data
    } catch (error) {
      console.error('Failed to update group status:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'new': return 'bg-red-100 text-red-800';
      case 'acknowledged': return 'bg-yellow-100 text-yellow-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      case 'ignored': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'error': return 'bg-orange-100 text-orange-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'info': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Error Groups</h1>
        <button 
          onClick={loadErrorGroups}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center space-x-4">
          <Filter className="h-5 w-5 text-gray-500" />
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
            <option value="ignored">Ignored</option>
          </select>
          <select
            value={filters.level}
            onChange={(e) => setFilters({ ...filters, level: e.target.value })}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="">All Levels</option>
            <option value="critical">Critical</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
        </div>
      </div>

      {/* Error Groups List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
          <div className="divide-y divide-gray-200">
            {groups.length === 0 ? (
              <div className="p-8 text-center">
                <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No error groups found</p>
              </div>
            ) : (
              groups.map(group => (
                <div key={group.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <Link 
                        to={`/errors/${group.id}`}
                        className="text-lg font-medium text-gray-900 hover:text-blue-600 truncate block"
                      >
                        {group.title}
                      </Link>
                      <div className="flex items-center space-x-4 mt-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(group.status)}`}>
                          {group.status}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelColor(group.level)}`}>
                          {group.level}
                        </span>
                        <span className="text-sm text-gray-500">
                          {group.count} occurrences
                        </span>
                        <span className="text-sm text-gray-500 flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {formatDate(group.last_seen)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {group.status === 'new' && (
                        <button
                          onClick={() => updateGroupStatus(group.id, 'acknowledged')}
                          className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                        >
                          Acknowledge
                        </button>
                      )}
                      {group.status === 'acknowledged' && (
                        <button
                          onClick={() => updateGroupStatus(group.id, 'resolved')}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ErrorList;
