import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, FileText } from 'lucide-react';

const Compliance = () => {
  const [compliance, setCompliance] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComplianceData();
  }, []);

  const fetchComplianceData = async () => {
    try {
      const [statusResponse, reportResponse] = await Promise.all([
              fetch('http://localhost:8000/api/compliance/'),
      fetch('http://localhost:8000/api/compliance/report')
      ]);
      
      const statusData = await statusResponse.json();
      const reportData = await reportResponse.json();
      
      setCompliance(statusData);
      setReport(reportData);
    } catch (error) {
      console.error('Error fetching compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFrameworkIcon = (framework) => {
    switch (framework.toLowerCase()) {
      case 'gdpr':
        return <Shield className="h-6 w-6 text-blue-500" />;
      case 'sox':
        return <FileText className="h-6 w-6 text-green-500" />;
      case 'hipaa':
        return <AlertTriangle className="h-6 w-6 text-purple-500" />;
      default:
        return <Shield className="h-6 w-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-800';
      case 'not_applicable':
        return 'bg-gray-100 text-gray-800';
      case 'non_compliant':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h1>
          <p className="text-gray-600">Monitor regulatory compliance across frameworks</p>
        </div>
        <button
          onClick={fetchComplianceData}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Clock className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Overall Compliance Score */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center">
          <div className="text-4xl font-bold text-blue-600 mb-2">
            {compliance?.compliance_score || 0}%
          </div>
          <div className="text-lg text-gray-600">Overall Compliance Score</div>
        </div>
      </div>

      {/* Framework Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {compliance?.frameworks && Object.entries(compliance.frameworks).map(([framework, data]) => (
          <div key={framework} className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                {getFrameworkIcon(framework)}
                <h3 className="text-lg font-semibold text-gray-900 capitalize">
                  {framework}
                </h3>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(data.status)}`}>
                {data.status}
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Score:</span>
                <span className="font-medium">{data.score}%</span>
              </div>
              
              {data.last_audit && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Audit:</span>
                  <span className="text-sm text-gray-500">
                    {new Date(data.last_audit).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Compliance Report */}
      {report && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Compliance Report</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {report.summary?.total_policies || 0}
              </div>
              <div className="text-sm text-gray-600">Total Policies</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {report.summary?.compliant_policies || 0}
              </div>
              <div className="text-sm text-gray-600">Compliant Policies</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {report.summary?.violations || 0}
              </div>
              <div className="text-sm text-gray-600">Violations</div>
            </div>
          </div>

          {/* Violations Details */}
          {report.details && Object.entries(report.details).map(([framework, violations]) => (
            violations.length > 0 && (
              <div key={framework} className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-2 capitalize">
                  {framework.replace('_', ' ')} Violations
                </h3>
                <ul className="space-y-2">
                  {violations.map((violation, index) => (
                    <li key={index} className="flex items-center space-x-2 text-sm text-red-600">
                      <AlertTriangle className="h-4 w-4" />
                      <span>{violation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )
          ))}
        </div>
      )}
    </div>
  );
};

export default Compliance; 