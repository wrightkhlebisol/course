import React from 'react';
import FailoverDashboard from './components/FailoverDashboard';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Active-Passive Failover Dashboard</h1>
        <p>Monitor your distributed log processing system</p>
      </header>
      <main>
        <FailoverDashboard />
      </main>
    </div>
  );
}

export default App;
