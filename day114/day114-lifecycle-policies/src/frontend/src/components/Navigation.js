import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, Settings, FileText } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/policies', label: 'Policies', icon: Settings },
    { path: '/reports', label: 'Reports', icon: FileText }
  ];

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h2>Lifecycle Manager</h2>
      </div>
      <div className="nav-links">
        {navItems.map(({ path, label, icon: Icon }) => (
          <Link
            key={path}
            to={path}
            className={`nav-link ${location.pathname === path ? 'active' : ''}`}
          >
            <Icon className="nav-icon" />
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
};

export default Navigation;
