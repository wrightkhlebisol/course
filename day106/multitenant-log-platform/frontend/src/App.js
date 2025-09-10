import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import TenantRegistrationPage from './pages/TenantRegistrationPage';
import './App.css';

function App() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing auth token
        const token = localStorage.getItem('authToken');
        const userData = localStorage.getItem('userData');
        
        if (token && userData) {
            setUser(JSON.parse(userData));
        }
        setLoading(false);
    }, []);

    const handleLogin = (userData, token) => {
        setUser(userData);
        localStorage.setItem('authToken', token);
        localStorage.setItem('userData', JSON.stringify(userData));
    };

    const handleLogout = () => {
        setUser(null);
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
    };

    if (loading) {
        return <div className="loading">Loading...</div>;
    }

    return (
        <Router>
            <div className="App">
                <Routes>
                    <Route 
                        path="/login" 
                        element={
                            user ? <Navigate to="/dashboard" /> : 
                            <LoginPage onLogin={handleLogin} />
                        } 
                    />
                    <Route 
                        path="/register" 
                        element={<TenantRegistrationPage />} 
                    />
                    <Route 
                        path="/dashboard" 
                        element={
                            user ? <DashboardPage user={user} onLogout={handleLogout} /> : 
                            <Navigate to="/login" />
                        } 
                    />
                    <Route path="/" element={<Navigate to="/dashboard" />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
