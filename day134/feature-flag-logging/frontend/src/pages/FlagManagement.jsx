import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Plus, Edit2, Trash2, ToggleLeft, ToggleRight, Save, X, Flag } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

const FlagCard = ({ flag, onEdit, onDelete, onToggle }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-900">{flag.name}</h3>
            <button
              onClick={() => onToggle(flag.id, !flag.enabled)}
              className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium ${
                flag.enabled
                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              }`}
            >
              {flag.enabled ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
              <span>{flag.enabled ? 'Enabled' : 'Disabled'}</span>
            </button>
          </div>
          {flag.description && (
            <p className="text-gray-600 mt-1">{flag.description}</p>
          )}
          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
            <span>Rollout: {flag.rollout_percentage}%</span>
            <span>Created: {new Date(flag.created_at).toLocaleDateString()}</span>
            {flag.updated_at !== flag.created_at && (
              <span>Updated: {new Date(flag.updated_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onEdit(flag)}
            className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-full"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(flag.id)}
            className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {flag.target_groups && flag.target_groups.length > 0 && (
        <div className="mt-3">
          <div className="flex flex-wrap gap-2">
            {flag.target_groups.map((group) => (
              <span key={group} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                {group}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const FlagForm = ({ flag, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: flag?.name || '',
    description: flag?.description || '',
    enabled: flag?.enabled || false,
    rollout_percentage: flag?.rollout_percentage || '0',
    target_groups: flag?.target_groups?.join(', ') || '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      ...formData,
      target_groups: formData.target_groups ? formData.target_groups.split(',').map(s => s.trim()) : []
    };
    onSubmit(data);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {flag ? 'Edit Feature Flag' : 'Create Feature Flag'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
              disabled={!!flag}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="enabled"
              checked={formData.enabled}
              onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
              className="mr-2"
            />
            <label htmlFor="enabled" className="text-sm font-medium text-gray-700">Enabled</label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Rollout Percentage (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={formData.rollout_percentage}
              onChange={(e) => setFormData({ ...formData, rollout_percentage: e.target.value })}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Target Groups (comma-separated)</label>
            <input
              type="text"
              value={formData.target_groups}
              onChange={(e) => setFormData({ ...formData, target_groups: e.target.value })}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="beta-users, premium-users"
            />
          </div>
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>{flag ? 'Update' : 'Create'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const FlagManagement = () => {
  const [editingFlag, setEditingFlag] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  
  const queryClient = useQueryClient();
  const { data: flags = [], isLoading } = useQuery('flags', api.getFlags);

  const createMutation = useMutation(api.createFlag, {
    onSuccess: () => {
      queryClient.invalidateQueries('flags');
      toast.success('Flag created successfully');
      setIsCreating(false);
    },
    onError: (error) => {
      toast.error('Failed to create flag');
    }
  });

  const updateMutation = useMutation(api.updateFlag, {
    onSuccess: () => {
      queryClient.invalidateQueries('flags');
      toast.success('Flag updated successfully');
      setEditingFlag(null);
    },
    onError: (error) => {
      toast.error('Failed to update flag');
    }
  });

  const deleteMutation = useMutation(api.deleteFlag, {
    onSuccess: () => {
      queryClient.invalidateQueries('flags');
      toast.success('Flag deleted successfully');
    },
    onError: (error) => {
      toast.error('Failed to delete flag');
    }
  });

  const handleCreate = (data) => {
    createMutation.mutate(data);
  };

  const handleUpdate = (data) => {
    updateMutation.mutate({ id: editingFlag.id, ...data });
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this flag?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleToggle = (id, enabled) => {
    updateMutation.mutate({ id, enabled });
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading flags...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Feature Flag Management</h1>
          <p className="text-gray-600">Create, edit, and manage your feature flags</p>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Create Flag</span>
        </button>
      </div>

      {flags.length === 0 ? (
        <div className="text-center py-12">
          <Flag className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No feature flags yet</h3>
          <p className="text-gray-500 mb-4">Get started by creating your first feature flag</p>
          <button
            onClick={() => setIsCreating(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Create Your First Flag
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {flags.map((flag) => (
            <FlagCard
              key={flag.id}
              flag={flag}
              onEdit={setEditingFlag}
              onDelete={handleDelete}
              onToggle={handleToggle}
            />
          ))}
        </div>
      )}

      {(isCreating || editingFlag) && (
        <FlagForm
          flag={editingFlag}
          onSubmit={isCreating ? handleCreate : handleUpdate}
          onCancel={() => {
            setIsCreating(false);
            setEditingFlag(null);
          }}
        />
      )}
    </div>
  );
};

export default FlagManagement;
