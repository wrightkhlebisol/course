import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

function TenantList() {
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTenants()
  }, [])

  const fetchTenants = async () => {
    try {
      const response = await axios.get('/api/tenants')
      setTenants(response.data)
    } catch (error) {
      console.error('Failed to fetch tenants:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleOffboard = async (tenantId) => {
    if (window.confirm('Are you sure you want to offboard this tenant? This action cannot be undone.')) {
      try {
        await axios.post(`/api/tenants/${tenantId}/offboard`)
        alert('Tenant offboarding initiated')
        fetchTenants() // Refresh list
      } catch (error) {
        alert('Failed to initiate offboarding')
        console.error('Offboarding error:', error)
      }
    }
  }

  if (loading) return <div className="loading">Loading tenants...</div>

  return (
    <div className="tenant-list">
      <div className="page-header">
        <h1>Tenant Management</h1>
        <Link to="/onboard" className="btn btn-primary">Onboard New Tenant</Link>
      </div>

      <div className="tenant-table">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Plan</th>
              <th>State</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map(tenant => (
              <tr key={tenant.id}>
                <td>{tenant.name}</td>
                <td>{tenant.email}</td>
                <td><span className={`plan-badge ${tenant.plan}`}>{tenant.plan}</span></td>
                <td><span className={`state-badge ${tenant.state}`}>{tenant.state}</span></td>
                <td>{new Date(tenant.created_at).toLocaleDateString()}</td>
                <td>
                  <Link to={`/tenants/${tenant.id}`} className="btn btn-sm">View</Link>
                  {tenant.state === 'active' && (
                    <button 
                      onClick={() => handleOffboard(tenant.id)}
                      className="btn btn-sm btn-danger"
                    >
                      Offboard
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {tenants.length === 0 && (
          <div className="empty-state">
            <p>No tenants found. <Link to="/onboard">Onboard your first tenant</Link></p>
          </div>
        )}
      </div>
    </div>
  )
}

export default TenantList
