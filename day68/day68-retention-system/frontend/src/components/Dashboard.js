import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Database, Shield, Clock, TrendingUp, Play, RotateCcw } from 'lucide-react';

const Dashboard = ({ metrics, onMetricsRefresh }) => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStep, setSimulationStep] = useState(0);
  const [simulationData, setSimulationData] = useState(null);

  const storageData = [
    { name: 'Hot Storage', value: 35, color: '#ff6b6b' },
    { name: 'Warm Storage', value: 45, color: '#4ecdc4' },
    { name: 'Cold Storage', value: 20, color: '#45b7d1' }
  ];

  const complianceData = [
    { framework: 'GDPR', score: 98 },
    { framework: 'SOX', score: 95 },
    { framework: 'HIPAA', score: 92 }
  ];

  const runSimulation = async () => {
    setIsSimulating(true);
    setSimulationStep(0);
    
    try {
      // Step 1: Start retention job
      setSimulationStep(1);
      const jobResponse = await fetch('http://localhost:8000/api/retention/simulate/start', { method: 'POST' });
      const jobData = await jobResponse.json();
      console.log('Job started:', jobData);
      
      // Update metrics after job start
      const metricsResponse1 = await fetch('http://localhost:8000/api/retention/metrics');
      const updatedMetrics1 = await metricsResponse1.json();
      setSimulationData(updatedMetrics1);
      if (onMetricsRefresh) onMetricsRefresh();
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Step 2: Process logs
      setSimulationStep(2);
      const processResponse = await fetch('http://localhost:8000/api/retention/simulate/process', { method: 'POST' });
      const processData = await processResponse.json();
      console.log('Logs processed:', processData);
      
      // Update metrics after processing
      const metricsResponse2 = await fetch('http://localhost:8000/api/retention/metrics');
      const updatedMetrics2 = await metricsResponse2.json();
      setSimulationData(updatedMetrics2);
      if (onMetricsRefresh) onMetricsRefresh();
      
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Step 3: Update storage
      setSimulationStep(3);
      const storageResponse = await fetch('http://localhost:8000/api/retention/simulate/storage', { method: 'POST' });
      const storageData = await storageResponse.json();
      console.log('Storage updated:', storageData);
      
      // Update metrics after storage update
      const metricsResponse3 = await fetch('http://localhost:8000/api/retention/metrics');
      const updatedMetrics3 = await metricsResponse3.json();
      setSimulationData(updatedMetrics3);
      if (onMetricsRefresh) onMetricsRefresh();
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Step 4: Complete simulation
      setSimulationStep(4);
      const completeResponse = await fetch('http://localhost:8000/api/retention/simulate/complete', { method: 'POST' });
      const completeData = await completeResponse.json();
      console.log('Simulation completed:', completeData);
      
      // Get final updated metrics
      const metricsResponse4 = await fetch('http://localhost:8000/api/retention/metrics');
      const updatedMetrics4 = await metricsResponse4.json();
      setSimulationData(updatedMetrics4);
      if (onMetricsRefresh) onMetricsRefresh();
      
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setIsSimulating(false);
      setSimulationStep(0);
    }
  };

  const resetSimulation = async () => {
    try {
      await fetch('http://localhost:8000/api/retention/simulate/reset', { method: 'POST' });
      setIsSimulating(false);
      setSimulationStep(0);
      setSimulationData(null);
      if (onMetricsRefresh) onMetricsRefresh();
    } catch (error) {
      console.error('Reset error:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Data Retention Dashboard</h1>
            <p className="text-gray-600">Monitor and manage your log retention policies</p>
          </div>
          <div className="flex items-center space-x-3">
            {isSimulating && (
              <div className="flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm font-medium">
                  {simulationStep === 1 && "Starting retention job..."}
                  {simulationStep === 2 && "Processing logs..."}
                  {simulationStep === 3 && "Updating storage..."}
                  {simulationStep === 4 && "Completing simulation..."}
                </span>
              </div>
            )}
            <button
              onClick={runSimulation}
              disabled={isSimulating}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                isSimulating
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              <Play className="h-4 w-4" />
              <span>Run Simulation</span>
            </button>
            <button
              onClick={resetSimulation}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Policies</p>
              <p className="text-3xl font-bold text-blue-600">{metrics?.total_policies || 0}</p>
            </div>
            <Database className="h-12 w-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Jobs</p>
              <p className={`text-3xl font-bold ${simulationData ? 'text-green-700 animate-pulse' : 'text-green-600'}`}>
                {(simulationData?.active_jobs ?? metrics?.active_jobs) || 0}
              </p>
            </div>
            <Clock className="h-12 w-12 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Storage Freed</p>
              <p className={`text-3xl font-bold ${simulationData ? 'text-purple-700 animate-pulse' : 'text-purple-600'}`}>
                {((simulationData?.storage_freed_gb ?? metrics?.storage_freed_gb) || 0).toFixed(1)} GB
              </p>
            </div>
            <TrendingUp className="h-12 w-12 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Compliance Score</p>
              <p className={`text-3xl font-bold ${simulationData ? 'text-orange-700 animate-pulse' : 'text-orange-600'}`}>
                {((simulationData?.compliance_score ?? metrics?.compliance_score) || 0).toFixed(1)}%
              </p>
            </div>
            <Shield className="h-12 w-12 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Storage Distribution */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={storageData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
              >
                {storageData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Compliance Scores */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Scores</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={complianceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="framework" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" fill="#4ecdc4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Simulation Status */}
      {isSimulating && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Simulation Progress</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${simulationStep >= 1 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className={`text-sm ${simulationStep >= 1 ? 'text-green-700 font-medium' : 'text-gray-500'}`}>
                Starting retention job...
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${simulationStep >= 2 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className={`text-sm ${simulationStep >= 2 ? 'text-green-700 font-medium' : 'text-gray-500'}`}>
                Processing logs and applying policies...
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${simulationStep >= 3 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className={`text-sm ${simulationStep >= 3 ? 'text-green-700 font-medium' : 'text-gray-500'}`}>
                Updating storage and metrics...
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${simulationStep >= 4 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
              <span className={`text-sm ${simulationStep >= 4 ? 'text-green-700 font-medium' : 'text-gray-500'}`}>
                Simulation completed!
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Retention Activity</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Debug logs cleanup completed</p>
              <p className="text-xs text-gray-500">2 hours ago • 500 MB freed</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Security logs archived</p>
              <p className="text-xs text-gray-500">6 hours ago • 1.2 GB moved to cold storage</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Policy evaluation started</p>
              <p className="text-xs text-gray-500">12 hours ago • Processing 10,000 logs</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 