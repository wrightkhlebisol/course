import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function App() {
  const [auditRecords, setAuditRecords] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    user_id: '',
    operation_type: '',
    resource_type: '',
    days: 30
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch audit records
      const recordsResponse = await axios.get(`${API_BASE_URL}/audit/records`, {
        params: filters,
        headers: {
          'X-User-ID': 'admin',
          'X-Session-ID': 'admin-session'
        }
      });

      // Fetch statistics
      const statsResponse = await axios.get(`${API_BASE_URL}/audit/statistics`, {
        params: { days: filters.days },
        headers: {
          'X-User-ID': 'admin',
          'X-Session-ID': 'admin-session'
        }
      });

      // Fetch verification
      const verificationResponse = await axios.get(`${API_BASE_URL}/audit/verify`, {
        headers: {
          'X-User-ID': 'admin',
          'X-Session-ID': 'admin-session'
        }
      });

      setAuditRecords(recordsResponse.data);
      setStatistics(statsResponse.data);
      setVerification(verificationResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const searchLogs = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/logs/search`, {
        query: 'sample',
        limit: 10
      }, {
        headers: {
          'X-User-ID': 'test-user',
          'X-Session-ID': 'test-session'
        }
      });
      
      alert(`Searched ${response.data.logs.length} logs - Check audit records!`);
      fetchData(); // Refresh to show new audit records
    } catch (err) {
      alert('Error searching logs: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="App">
        <div className="header">
          <h1>🔍 Audit Trail System</h1>
          <p>Immutable Access Tracking for Distributed Log Processing</p>
        </div>
        <div className="loading">Loading audit data...</div>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="header">
        <h1>🔍 Audit Trail System</h1>
        <p>Immutable Access Tracking for Distributed Log Processing</p>
      </div>

      <div className="container">
        {error && <div className="error">{error}</div>}

        {/* Statistics Cards */}
        {statistics && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{statistics.total_accesses}</div>
              <div className="stat-label">Total Accesses</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{statistics.successful_accesses}</div>
              <div className="stat-label">Successful Accesses</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{statistics.failed_accesses}</div>
              <div className="stat-label">Failed Accesses</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{statistics.unique_users}</div>
              <div className="stat-label">Unique Users</div>
            </div>
          </div>
        )}

        {/* Integrity Verification */}
        {verification && (
          <div className="card">
            <h2>🔒 Audit Chain Integrity</h2>
            <div className={`status ${verification.integrity_status === 'VALID' ? 'success' : 'error'}`}>
              Status: {verification.integrity_status}
            </div>
            <p>Verified {verification.verified_records} of {verification.total_records} records</p>
            {verification.failed_records > 0 && (
              <div className="error">
                ⚠️ {verification.failed_records} records failed integrity check
              </div>
            )}
          </div>
        )}

        {/* Demo Actions */}
        <div className="card">
          <h2>🎮 Demo Actions</h2>
          <p>Trigger log access to generate audit records:</p>
          <button className="btn" onClick={searchLogs}>
            Search Sample Logs
          </button>
        </div>

        {/* Filters */}
        <div className="card">
          <h2>🔍 Audit Record Filters</h2>
          <div className="filters">
            <input
              type="text"
              placeholder="User ID"
              className="filter-input"
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
            />
            <select
              className="filter-input"
              value={filters.operation_type}
              onChange={(e) => handleFilterChange('operation_type', e.target.value)}
            >
              <option value="">All Operations</option>
              <option value="READ">READ</option>
              <option value="SEARCH">SEARCH</option>
              <option value="DOWNLOAD">DOWNLOAD</option>
            </select>
            <select
              className="filter-input"
              value={filters.resource_type}
              onChange={(e) => handleFilterChange('resource_type', e.target.value)}
            >
              <option value="">All Resources</option>
              <option value="LOG">LOG</option>
              <option value="AUDIT_RECORD">AUDIT_RECORD</option>
              <option value="USER_LOG">USER_LOG</option>
            </select>
            <input
              type="number"
              placeholder="Days"
              className="filter-input"
              value={filters.days}
              onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
            />
            <button className="btn" onClick={fetchData}>
              Apply Filters
            </button>
          </div>
        </div>

        {/* Audit Records Table */}
        <div className="card">
          <h2>📋 Audit Records</h2>
          {auditRecords.length === 0 ? (
            <p>No audit records found. Try the demo actions above!</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>User</th>
                  <th>Operation</th>
                  <th>Resource</th>
                  <th>Status</th>
                  <th>IP Address</th>
                  <th>Records</th>
                </tr>
              </thead>
              <tbody>
                {auditRecords.map((record) => (
                  <tr key={record.id}>
                    <td>{new Date(record.created_at).toLocaleString()}</td>
                    <td>{record.user_id}</td>
                    <td>{record.operation_type}</td>
                    <td>{record.resource_type}</td>
                    <td className={record.success ? 'status-success' : 'status-error'}>
                      {record.success ? 'SUCCESS' : 'FAILED'}
                    </td>
                    <td>{record.ip_address}</td>
                    <td>{record.records_returned || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
