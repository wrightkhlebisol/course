import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

function TenantDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tenant, setTenant] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTenantDetail()
  }, [id])

  const fetchTenantDetail = async () => {
    try {
      const response = await axios.get(`/api/tenants/${id}`)
      setTenant(response.data)
    } catch (error) {
      console.error('Failed to fetch tenant details:', error)
      if (error.response?.status === 404) {
        alert('Tenant not found')
        navigate('/tenants')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleOffboard = async () => {
    if (window.confirm('Are you sure you want to offboard this tenant? This action cannot be undone.')) {
      try {
        await axios.post(`/api/tenants/${id}/offboard`)
        alert('Tenant offboarding initiated')
        navigate('/tenants')
      } catch (error) {
        alert('Failed to initiate offboarding')
        console.error('Offboarding error:', error)
      }
    }
  }

  if (loading) return <div className="loading">Loading tenant details...</div>
  if (!tenant) return <div className="error">Tenant not found</div>

  return (
    <div className="tenant-detail">
      <div className="page-header">
        <h1>{tenant.name}</h1>
        <div className="header-actions">
          <button onClick={() => navigate('/tenants')} className="btn btn-secondary">Back to List</button>
          {tenant.state === 'active' && (
            <button onClick={handleOffboard} className="btn btn-danger">Offboard Tenant</button>
          )}
        </div>
      </div>

      <div className="detail-grid">
        <div className="info-section">
          <h3>Basic Information</h3>
          <div className="info-item">
            <label>Name:</label>
            <span>{tenant.name}</span>
          </div>
          <div className="info-item">
            <label>Email:</label>
            <span>{tenant.email}</span>
          </div>
          <div className="info-item">
            <label>Plan:</label>
            <span className={`plan-badge ${tenant.plan}`}>{tenant.plan}</span>
          </div>
          <div className="info-item">
            <label>State:</label>
            <span className={`state-badge ${tenant.state}`}>{tenant.state}</span>
          </div>
          <div className="info-item">
            <label>Created:</label>
            <span>{new Date(tenant.created_at).toLocaleString()}</span>
          </div>
          {tenant.updated_at && (
            <div className="info-item">
              <label>Last Updated:</label>
              <span>{new Date(tenant.updated_at).toLocaleString()}</span>
            </div>
          )}
        </div>

        <div className="security-section">
          <h3>Security & Access</h3>
          <div className="info-item">
            <label>API Key:</label>
            <span className="api-key">{tenant.api_key || 'Not generated'}</span>
          </div>
          <div className="info-item">
            <label>Access Level:</label>
            <span>{tenant.plan === 'enterprise' ? 'Full Admin' : 'Standard'}</span>
          </div>
        </div>

        <div className="resources-section">
          <h3>Resource Usage</h3>
          <div className="info-item">
            <label>Storage Used:</label>
            <span>{tenant.resources?.storage_used_gb || 0} GB</span>
          </div>
          <div className="info-item">
            <label>Logs Today:</label>
            <span>{tenant.resources?.logs_ingested_today || 0}</span>
          </div>
          <div className="info-item">
            <label>Active Streams:</label>
            <span>{tenant.resources?.active_streams || 0}</span>
          </div>
          <div className="info-item">
            <label>Last Activity:</label>
            <span>{tenant.resources?.last_activity ? new Date(tenant.resources.last_activity).toLocaleString() : 'Never'}</span>
          </div>
        </div>

        <div className="config-section">
          <h3>Configuration</h3>
          <pre className="config-display">
            {JSON.stringify(tenant.config, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default TenantDetail
