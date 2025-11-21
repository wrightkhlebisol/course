import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Search, Filter, Calendar, User, Activity } from 'lucide-react';
import api from '../services/api';

const LogEntry = ({ log }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getEventColor = (eventType) => {
    switch (eventType) {
      case 'create': return 'bg-green-100 text-green-800';
      case 'update': return 'bg-blue-100 text-blue-800';
      case 'delete': return 'bg-red-100 text-red-800';
      case 'evaluate': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatState = (state) => {
    if (!state) return 'N/A';
    if (typeof state === 'object') {
      return JSON.stringify(state, null, 2);
    }
    return String(state);
  };

  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      <div 
        className="p-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className={`px-2 py-1 text-xs rounded-full font-medium ${getEventColor(log.event_type)}`}>
              {log.event_type}
            </span>
            <span className="font-medium text-gray-900">{log.flag_name}</span>
            <span className="text-sm text-gray-500">
              {new Date(log.timestamp).toLocaleString()}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            {log.user_id && (
              <span className="flex items-center space-x-1">
                <User className="w-3 h-3" />
                <span>{log.user_id}</span>
              </span>
            )}
          </div>
        </div>
      </div>
      
      {isExpanded && (
        <div className="px-4 pb-4 border-t bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {log.previous_state && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Previous State</h4>
                <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-40">
                  {formatState(log.previous_state)}
                </pre>
              </div>
            )}
            {log.new_state && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">New State</h4>
                <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-40">
                  {formatState(log.new_state)}
                </pre>
              </div>
            )}
          </div>
          
          {log.context && Object.keys(log.context).length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Context</h4>
              <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-40">
                {JSON.stringify(log.context, null, 2)}
              </pre>
            </div>
          )}
          
          <div className="mt-4 text-xs text-gray-500 space-y-1">
            <div>Event ID: {log.id}</div>
            <div>Flag ID: {log.flag_id}</div>
            {log.user_agent && <div>User Agent: {log.user_agent}</div>}
            {log.ip_address && <div>IP Address: {log.ip_address}</div>}
          </div>
        </div>
      )}
    </div>
  );
};

const AuditLogs = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [eventFilter, setEventFilter] = useState('all');
  
  const { data: logs = [], isLoading } = useQuery('recentLogs', api.getRecentLogs, {
    refetchInterval: 10000
  });

  const filteredLogs = logs.filter(log => {
    const matchesSearch = !searchTerm || 
      log.flag_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.event_type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = eventFilter === 'all' || log.event_type === eventFilter;
    
    return matchesSearch && matchesFilter;
  });

  const eventTypes = ['all', ...new Set(logs.map(log => log.event_type))];

  if (isLoading) {
    return <div className="text-center py-8">Loading audit logs...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600">Track all feature flag activities and changes</p>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border space-y-4 md:space-y-0 md:flex md:items-center md:justify-between">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {eventTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Events' : type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <Activity className="w-4 h-4" />
          <span>{filteredLogs.length} events found</span>
        </div>
      </div>

      {/* Logs */}
      {filteredLogs.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No logs found</h3>
          <p className="text-gray-500">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLogs.map((log) => (
            <LogEntry key={log.id} log={log} />
          ))}
        </div>
      )}
    </div>
  );
};

export default AuditLogs;
