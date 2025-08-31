import React from 'react';

const SystemStatus = ({ status }) => {
  if (!status) return <div>Loading...</div>;

  // Handle 429 responses or incomplete status
  if (status.error || !status.backpressure) {
    return (
      <div className="system-status">
        <h3>🎯 System Status Overview</h3>
        <div className="status-error">
          <div className="status-card">
            <h4>⚡ System Under Load</h4>
            <div className="status-indicator" style={{ backgroundColor: '#fbbc04' }}>
              BACKPRESSURE ACTIVE
            </div>
            <div className="status-details">
              <div>{status.message || 'System is managing high load'}</div>
              <div>Retry after: {status.retry_after || 'a moment'}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { backpressure, processor, circuit_breaker } = status;

  const getPressureLevelColor = (level) => {
    switch (level) {
      case 'normal': return '#34a853';
      case 'pressure': return '#fbbc04';
      case 'overload': return '#ea4335';
      case 'recovery': return '#4285f4';
      default: return '#666';
    }
  };

  const getCircuitStateColor = (state) => {
    switch (state) {
      case 'closed': return '#34a853';
      case 'half_open': return '#fbbc04';
      case 'open': return '#ea4335';
      default: return '#666';
    }
  };

  return (
    <div className="system-status">
      <h3>🎯 System Status Overview</h3>
      
      <div className="status-grid">
        <div className="status-card">
          <h4>Backpressure Level</h4>
          <div 
            className="status-indicator"
            style={{ backgroundColor: getPressureLevelColor(backpressure.pressure_level) }}
          >
            {backpressure.pressure_level.toUpperCase()}
          </div>
          <div className="status-details">
            <div>Throttle Rate: {(backpressure.throttle_rate * 100).toFixed(1)}%</div>
            <div>Pressure Score: {(backpressure.pressure_score * 100).toFixed(1)}%</div>
          </div>
        </div>

        <div className="status-card">
          <h4>Queue Status</h4>
          <div className="queue-info">
            <div className="queue-bar">
              <div 
                className="queue-fill"
                style={{ 
                  width: `${(backpressure.queue_size / backpressure.max_queue_size) * 100}%`,
                  backgroundColor: backpressure.queue_size > backpressure.max_queue_size * 0.8 ? '#ea4335' : '#34a853'
                }}
              ></div>
            </div>
            <div className="queue-numbers">
              {backpressure.queue_size} / {backpressure.max_queue_size}
            </div>
          </div>
        </div>

        <div className="status-card">
          <h4>Circuit Breaker</h4>
          <div 
            className="status-indicator"
            style={{ backgroundColor: getCircuitStateColor(circuit_breaker.state) }}
          >
            {circuit_breaker.state.replace('_', ' ').toUpperCase()}
          </div>
          <div className="status-details">
            <div>Failures: {circuit_breaker.failure_count}</div>
            <div>Successes: {circuit_breaker.success_count}</div>
          </div>
        </div>

        <div className="status-card">
          <h4>Processing Stats</h4>
          <div className="processing-stats">
            <div className="stat-row">
              <span>✅ Processed:</span>
              <span>{processor.processed_count}</span>
            </div>
            <div className="stat-row">
              <span>❌ Dropped:</span>
              <span>{processor.dropped_count}</span>
            </div>
            <div className="stat-row">
              <span>⚠️ Errors:</span>
              <span>{processor.error_count}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemStatus;
