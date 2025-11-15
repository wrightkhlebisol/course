import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, User, Tag } from 'lucide-react';
import api from '../../services/api';

const ErrorDetail = () => {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const [group, setGroup] = useState(null);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedError, setSelectedError] = useState(null);

  useEffect(() => {
    loadErrorDetail();
  }, [groupId]);

  const loadErrorDetail = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/errors/groups/${groupId}`);
      setGroup(response.data.group);
      setErrors(response.data.errors);
      if (response.data.errors.length > 0) {
        setSelectedError(response.data.errors[0]);
      }
    } catch (error) {
      console.error('Failed to load error detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="text-center">
        <p className="text-gray-500">Error group not found</p>
        <button 
          onClick={() => navigate('/errors')}
          className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Back to Error Groups
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button 
          onClick={() => navigate('/errors')}
          className="flex items-center text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5 mr-1" />
          Back
        </button>
        <h1 className="text-3xl font-bold text-gray-900 truncate">{group.title}</h1>
      </div>

      {/* Error Group Info */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm font-medium text-gray-600">Status</p>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium mt-1 ${
              group.status === 'new' ? 'bg-red-100 text-red-800' :
              group.status === 'acknowledged' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {group.status}
            </span>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Level</p>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium mt-1 ${
              group.level === 'critical' ? 'bg-red-100 text-red-800' :
              group.level === 'error' ? 'bg-orange-100 text-orange-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              {group.level}
            </span>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Occurrences</p>
            <p className="text-lg font-semibold text-gray-900 mt-1">{group.count}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Platform</p>
            <p className="text-lg font-semibold text-gray-900 mt-1">{group.platform || 'N/A'}</p>
          </div>
        </div>
        
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-600 flex items-center">
                <Clock className="h-4 w-4 mr-1" />
                First Seen
              </p>
              <p className="text-sm text-gray-900 mt-1">{formatDate(group.first_seen)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 flex items-center">
                <Clock className="h-4 w-4 mr-1" />
                Last Seen
              </p>
              <p className="text-sm text-gray-900 mt-1">{formatDate(group.last_seen)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Instances */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Error List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Occurrences</h3>
          </div>
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {errors.map(error => (
              <div 
                key={error.id}
                onClick={() => setSelectedError(error)}
                className={`p-4 cursor-pointer hover:bg-gray-50 ${
                  selectedError?.id === error.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">
                    {formatDate(error.timestamp)}
                  </span>
                  {error.trace_id && (
                    <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">
                      Trace: {error.trace_id.slice(0, 8)}...
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1 truncate">{error.message}</p>
                {error.user_id && (
                  <div className="flex items-center mt-1">
                    <User className="h-3 w-3 text-gray-400 mr-1" />
                    <span className="text-xs text-gray-500">{error.user_id}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Error Details */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Error Details</h3>
          </div>
          {selectedError ? (
            <div className="p-4 space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-600 mb-2">Message</h4>
                <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">{selectedError.message}</p>
              </div>
              
              {selectedError.stack_trace && (
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-2">Stack Trace</h4>
                  <pre className="text-xs text-gray-900 bg-gray-50 p-3 rounded-md overflow-x-auto max-h-64">
                    {selectedError.stack_trace}
                  </pre>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Environment</h4>
                  <p className="text-sm text-gray-900">{selectedError.environment}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-1">Release</h4>
                  <p className="text-sm text-gray-900">{selectedError.release || 'N/A'}</p>
                </div>
              </div>
              
              {Object.keys(selectedError.context || {}).length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-600 mb-2">Context</h4>
                  <pre className="text-xs text-gray-900 bg-gray-50 p-3 rounded-md overflow-x-auto">
                    {JSON.stringify(selectedError.context, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">
              Select an error occurrence to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorDetail;
