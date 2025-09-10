import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function TenantRegistrationPage() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        name: '',
        domain: '',
        service_tier: 'BASIC',
        admin_email: '',
        admin_username: '',
        admin_password: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleInputChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await axios.post('/api/v1/tenants/', formData);
            setSuccess(true);
            setTimeout(() => navigate('/login'), 2000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="login-container">
                <div className="login-form">
                    <h2>Registration Successful!</h2>
                    <div className="success">
                        Your tenant has been created successfully. 
                        Redirecting to login...
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="login-container">
            <form className="login-form" onSubmit={handleSubmit}>
                <h2>Create New Tenant</h2>
                
                <div className="form-group">
                    <label>Company Name</label>
                    <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleInputChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Domain</label>
                    <input
                        type="text"
                        name="domain"
                        value={formData.domain}
                        onChange={handleInputChange}
                        placeholder="your-company.com"
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Service Tier</label>
                    <select
                        name="service_tier"
                        value={formData.service_tier}
                        onChange={handleInputChange}
                    >
                        <option value="BASIC">Basic</option>
                        <option value="PREMIUM">Premium</option>
                        <option value="ENTERPRISE">Enterprise</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>Admin Email</label>
                    <input
                        type="email"
                        name="admin_email"
                        value={formData.admin_email}
                        onChange={handleInputChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Admin Username</label>
                    <input
                        type="text"
                        name="admin_username"
                        value={formData.admin_username}
                        onChange={handleInputChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Admin Password</label>
                    <input
                        type="password"
                        name="admin_password"
                        value={formData.admin_password}
                        onChange={handleInputChange}
                        required
                    />
                </div>

                <button type="submit" className="btn" disabled={loading}>
                    {loading ? 'Creating Tenant...' : 'Create Tenant'}
                </button>

                {error && <div className="error">{error}</div>}

                <Link to="/login" className="link">
                    Already have an account? Login here
                </Link>
            </form>
        </div>
    );
}

export default TenantRegistrationPage;
