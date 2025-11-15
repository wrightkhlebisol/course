import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard/Dashboard';
import ErrorList from './components/ErrorList/ErrorList';
import ErrorDetail from './components/ErrorDetail/ErrorDetail';
import Navigation from './components/Navigation';
import './App.css';

function App() {
  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <div className="App min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/errors" element={<ErrorList />} />
            <Route path="/errors/:groupId" element={<ErrorDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
