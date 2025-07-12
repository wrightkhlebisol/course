import React, { useState } from 'react';

const LoadTester = ({ onTestStart }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [testConfig, setTestConfig] = useState({
    duration_seconds: 30,
    requests_per_second: 100,
    spike_multiplier: 5.0
  });

  const startLoadTest = async () => {
    setIsRunning(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/test/load', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testConfig),
      });

      const result = await response.json();
      console.log('Load test started:', result);
      
      onTestStart(); // Refresh system status
      
      // Auto-stop after test duration
      setTimeout(() => {
        setIsRunning(false);
      }, testConfig.duration_seconds * 1000);
      
    } catch (error) {
      console.error('Failed to start load test:', error);
      setIsRunning(false);
    }
  };

  const createTrafficSpike = async () => {
    setIsRunning(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/test/spike', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      console.log('Traffic spike initiated:', result);
      
      onTestStart(); // Refresh system status
      
      // Auto-stop after 10 seconds (spike duration)
      setTimeout(() => {
        setIsRunning(false);
      }, 10000);
      
    } catch (error) {
      console.error('Failed to create traffic spike:', error);
      setIsRunning(false);
    }
  };

  return (
    <div className="load-tester">
      <h3>⚡ Load Testing & Traffic Spikes</h3>
      
      <div className="test-section">
        <h4>Gradual Load Test</h4>
        <p>Tests backpressure response to increasing load over time</p>
        
        <div className="config-grid">
          <div className="config-item">
            <label>Duration (seconds):</label>
            <input
              type="number"
              value={testConfig.duration_seconds}
              onChange={(e) => setTestConfig({
                ...testConfig,
                duration_seconds: parseInt(e.target.value)
              })}
              min="10"
              max="300"
              disabled={isRunning}
            />
          </div>
          
          <div className="config-item">
            <label>Base RPS:</label>
            <input
              type="number"
              value={testConfig.requests_per_second}
              onChange={(e) => setTestConfig({
                ...testConfig,
                requests_per_second: parseInt(e.target.value)
              })}
              min="10"
              max="1000"
              disabled={isRunning}
            />
          </div>
          
          <div className="config-item">
            <label>Spike Multiplier:</label>
            <input
              type="number"
              step="0.5"
              value={testConfig.spike_multiplier}
              onChange={(e) => setTestConfig({
                ...testConfig,
                spike_multiplier: parseFloat(e.target.value)
              })}
              min="1.0"
              max="20.0"
              disabled={isRunning}
            />
          </div>
        </div>
        
        <button 
          onClick={startLoadTest}
          disabled={isRunning}
          className="load-test-button"
        >
          {isRunning ? 'Running Load Test...' : 'Start Load Test'}
        </button>
      </div>

      <div className="test-section">
        <h4>Instant Traffic Spike</h4>
        <p>Creates sudden 10x traffic increase to test emergency backpressure</p>
        
        <button 
          onClick={createTrafficSpike}
          disabled={isRunning}
          className="spike-button"
        >
          {isRunning ? 'Spike in Progress...' : 'Create Traffic Spike'}
        </button>
      </div>

      <div className="test-info">
        <h4>🎯 What to Watch For:</h4>
        <ul>
          <li><strong>Normal → Pressure:</strong> Throttle rate decreases gradually</li>
          <li><strong>Pressure → Overload:</strong> Aggressive throttling activates</li>
          <li><strong>Queue Management:</strong> Size stays within limits</li>
          <li><strong>Intelligent Dropping:</strong> Lower priority logs dropped first</li>
          <li><strong>Recovery:</strong> Gradual return to normal operation</li>
        </ul>
      </div>
    </div>
  );
};

export default LoadTester;
