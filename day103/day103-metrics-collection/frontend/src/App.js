import React, { useState, useEffect } from 'react';
import styled, { createGlobalStyle } from 'styled-components';
import MetricsCharts from './components/MetricsCharts';
import AlertsPanel from './components/AlertsPanel';
import SystemOverview from './components/SystemOverview';

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
  }
`;

const Container = styled.div`
  min-height: 100vh;
  padding: 20px;
`;

const Header = styled.header`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const Title = styled.h1`
  color: #2d3748;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 8px;
`;

const Subtitle = styled.p`
  color: #718096;
  font-size: 1.1rem;
`;

const Dashboard = styled.div`
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 24px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const MainContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const StatusIndicator = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  background: ${props => props.$status === 'healthy' ? '#48bb78' : '#f56565'};
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
`;

function App() {
  const [systemStatus, setSystemStatus] = useState('healthy');
  const [metricsData, setMetricsData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [, setWsConnection] = useState(null);

  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000; // 3 seconds

    // Fetch initial metrics data
    const fetchInitialMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/metrics/current');
        const data = await response.json();
        console.log('Initial metrics fetched:', data);
        setMetricsData(data);
      } catch (error) {
        console.error('Failed to fetch initial metrics:', error);
      }
    };

    const connectWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/ws/metrics');
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setWsConnection(ws);
          setSystemStatus('healthy');
          reconnectAttempts = 0; // Reset on successful connection
        };
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          if (data.type === 'metrics_update') {
            console.log('Setting metrics data:', data.metrics);
            setMetricsData(data.metrics);
            setAlerts(data.alerts || []);
          } else if (data.type === 'alert') {
            setAlerts(prev => [...prev, data.alert]);
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setSystemStatus('error');
        };
        
        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setSystemStatus('disconnected');
          setWsConnection(null);
          
          // Attempt to reconnect if we haven't exceeded max attempts
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts}) in ${reconnectDelay/1000} seconds...`);
            reconnectTimeout = setTimeout(connectWebSocket, reconnectDelay);
          } else {
            console.log('Max reconnection attempts reached. Please refresh the page.');
            setSystemStatus('error');
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        setSystemStatus('error');
      }
    };

    // Fetch initial metrics and connect WebSocket
    fetchInitialMetrics();
    connectWebSocket();
    
    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    };
  }, []);

  return (
    <>
      <GlobalStyle />
      <Container>
        <Header>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title>Distributed Log Processing Metrics</Title>
              <Subtitle>Real-time performance monitoring and alerting</Subtitle>
            </div>
            <StatusIndicator $status={systemStatus}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%', 
                background: 'currentColor',
                animation: 'pulse 2s infinite'
              }} />
              System {systemStatus}
            </StatusIndicator>
          </div>
        </Header>
        
        <Dashboard>
          <MainContent>
            <SystemOverview metricsData={metricsData} />
            <MetricsCharts metricsData={metricsData} />
          </MainContent>
          <AlertsPanel alerts={alerts} />
        </Dashboard>
      </Container>
    </>
  );
}

export default App;
