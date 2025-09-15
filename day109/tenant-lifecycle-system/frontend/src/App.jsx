import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import TenantList from './pages/TenantList'
import TenantDetail from './pages/TenantDetail'
import OnboardTenant from './pages/OnboardTenant'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-brand">
            <h2>🏢 Tenant Lifecycle Management</h2>
          </div>
          <div className="nav-links">
            <Link to="/">Dashboard</Link>
            <Link to="/tenants">Tenants</Link>
            <Link to="/onboard">Onboard New</Link>
          </div>
        </nav>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tenants" element={<TenantList />} />
            <Route path="/tenants/:id" element={<TenantDetail />} />
            <Route path="/onboard" element={<OnboardTenant />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
