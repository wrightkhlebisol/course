import React from 'react';
import styled from 'styled-components';

const AlertsContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  height: fit-content;
`;

const AlertItem = styled.div`
  background: ${props => {
    switch(props.level) {
      case 'critical': return 'linear-gradient(135deg, #ff6b6b, #ee5a52)';
      case 'warning': return 'linear-gradient(135deg, #ffa726, #fb8c00)';
      default: return 'linear-gradient(135deg, #42a5f5, #1e88e5)';
    }
  }};
  color: white;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
`;

const AlertLevel = styled.div`
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 4px;
  opacity: 0.9;
`;

const AlertMessage = styled.div`
  font-size: 0.9rem;
  margin-bottom: 8px;
  line-height: 1.4;
`;

const AlertValue = styled.div`
  font-size: 1.1rem;
  font-weight: 700;
`;

const NoAlertsMessage = styled.div`
  text-align: center;
  color: #718096;
  padding: 40px 20px;
  font-style: italic;
`;

const AlertsPanel = ({ alerts = [] }) => {
  return (
    <AlertsContainer>
      <h3 style={{ marginBottom: '20px', color: '#2d3748', fontSize: '1.3rem', fontWeight: '600' }}>
        Active Alerts ({alerts.length})
      </h3>
      
      {alerts.length === 0 ? (
        <NoAlertsMessage>
          🎉 No active alerts<br/>
          <small>All systems operating normally</small>
        </NoAlertsMessage>
      ) : (
        alerts.map((alert, index) => (
          <AlertItem key={alert.id || index} level={alert.level}>
            <AlertLevel>{alert.level}</AlertLevel>
            <AlertMessage>{alert.message}</AlertMessage>
            <AlertValue>Current: {alert.current_value?.toFixed(1)}</AlertValue>
          </AlertItem>
        ))
      )}
    </AlertsContainer>
  );
};

export default AlertsPanel;
