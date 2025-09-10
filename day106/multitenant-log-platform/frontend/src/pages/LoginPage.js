import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

function LoginPage({ onLogin }) {
    const [formData, setFormData] = useState({
        tenant_domain: '',
        username: '',
        password: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

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
            const response = await axios.post('/api/v1/tenants/login', formData);
            onLogin({
                tenant_id: response.data.tenant_id,
                username: response.data.username,
                tenant_domain: formData.tenant_domain
            }, response.data.access_token);
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <form className="login-form" onSubmit={handleSubmit}>
                <h2>Login to Your Tenant</h2>
                
                <div className="form-group">
                    <label>Tenant Domain</label>
                    <input
                        type="text"
                        name="tenant_domain"
                        value={formData.tenant_domain}
                        onChange={handleInputChange}
                        placeholder="your-company.com"
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Username</label>
                    <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleInputChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>Password</label>
                    <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleInputChange}
                        required
                    />
                </div>

                <button type="submit" className="btn" disabled={loading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>

                {error && <div className="error">{error}</div>}

                <Link to="/register" className="link">
                    Don't have a tenant? Register here
                </Link>
            </form>
        </div>
    );
}

export default LoginPage;
