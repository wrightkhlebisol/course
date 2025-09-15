import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import axios from 'axios'

function OnboardTenant() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = async (data) => {
    setLoading(true)
    try {
      const response = await axios.post('/api/tenants/onboard', {
        name: data.name,
        email: data.email,
        plan: data.plan,
        config: {
          log_retention_days: parseInt(data.retention_days),
          alert_email: data.alert_email,
          custom_domain: data.custom_domain
        }
      })
      
      alert(`Tenant onboarding initiated! Tenant ID: ${response.data.tenant_id}`)
      navigate('/tenants')
    } catch (error) {
      alert('Failed to initiate tenant onboarding')
      console.error('Onboarding error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="onboard-tenant">
      <div className="page-header">
        <h1>Onboard New Tenant</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="onboard-form">
        <div className="form-section">
          <h3>Basic Information</h3>
          
          <div className="form-group">
            <label>Organization Name *</label>
            <input
              type="text"
              {...register('name', { required: 'Organization name is required' })}
              placeholder="Enter organization name"
            />
            {errors.name && <span className="error">{errors.name.message}</span>}
          </div>

          <div className="form-group">
            <label>Admin Email *</label>
            <input
              type="email"
              {...register('email', { 
                required: 'Email is required',
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: 'Invalid email format'
                }
              })}
              placeholder="admin@organization.com"
            />
            {errors.email && <span className="error">{errors.email.message}</span>}
          </div>

          <div className="form-group">
            <label>Service Plan *</label>
            <select {...register('plan', { required: 'Please select a plan' })}>
              <option value="">Select a plan</option>
              <option value="basic">Basic - $99/month</option>
              <option value="pro">Pro - $299/month</option>
              <option value="enterprise">Enterprise - Custom</option>
            </select>
            {errors.plan && <span className="error">{errors.plan.message}</span>}
          </div>
        </div>

        <div className="form-section">
          <h3>Configuration</h3>
          
          <div className="form-group">
            <label>Log Retention (days)</label>
            <select {...register('retention_days')}>
              <option value="30">30 days</option>
              <option value="90">90 days</option>
              <option value="180">180 days</option>
              <option value="365">1 year</option>
            </select>
          </div>

          <div className="form-group">
            <label>Alert Email</label>
            <input
              type="email"
              {...register('alert_email')}
              placeholder="alerts@organization.com"
            />
          </div>

          <div className="form-group">
            <label>Custom Domain (optional)</label>
            <input
              type="text"
              {...register('custom_domain')}
              placeholder="logs.organization.com"
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/tenants')} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? 'Initiating Onboarding...' : 'Start Onboarding'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default OnboardTenant
