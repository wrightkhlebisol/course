import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Flag, BarChart3, FileText } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', name: 'Dashboard', icon: BarChart3 },
    { path: '/flags', name: 'Feature Flags', icon: Flag },
    { path: '/logs', name: 'Audit Logs', icon: FileText },
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2">
              <Flag className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">FeatureFlag Logger</span>
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
                        ? 'text-blue-600 bg-blue-50'
                        : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
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
