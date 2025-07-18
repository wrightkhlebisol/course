import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Database, Shield, Clock, Settings, FileText } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Database },
    { path: '/policies', label: 'Policies', icon: Settings },
    { path: '/jobs', label: 'Jobs', icon: Clock },
    { path: '/compliance', label: 'Compliance', icon: Shield },
    { path: '/logs', label: 'Logs', icon: FileText }
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2">
              <Database className="h-8 w-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Retention System</h1>
            </div>
            
            <div className="flex space-x-6">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 