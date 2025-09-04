import React from 'react';
import styled from 'styled-components';

const OverviewContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
`;

const MetricCard = styled.div`
  background: linear-gradient(135deg, ${props => props.$gradient});
  border-radius: 12px;
  padding: 20px;
  color: white;
  text-align: center;
`;

const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 8px;
`;

const MetricLabel = styled.div`
  font-size: 0.9rem;
  opacity: 0.9;
`;

const SystemOverview = ({ metricsData }) => {
  console.log('SystemOverview received metricsData:', metricsData);
  
  const getMetricValue = (path, defaultValue = 0) => {
    if (!metricsData) {
      console.log('No metricsData, returning default:', defaultValue);
      return defaultValue;
    }
    
    // Handle the actual data structure from the API
    if (path.startsWith('system_metrics.')) {
      const metricKey = path.replace('system_metrics.', '');
      const value = metricsData.system_metrics?.[metricKey];
      if (value !== undefined) {
        console.log(`Found system metric ${metricKey}:`, value);
        return value;
      }
    } else if (path.startsWith('application_metrics.')) {
      const metricKey = path.replace('application_metrics.', '');
      const value = metricsData.application_metrics?.[metricKey];
      if (value !== undefined) {
        console.log(`Found application metric ${metricKey}:`, value);
        return value;
      }
    }
    
    console.log(`Metric not found for path ${path}, returning default:`, defaultValue);
    return defaultValue;
  };

  const formatNumber = (num, decimals = 1) => {
    return typeof num === 'number' ? num.toFixed(decimals) : '0.0';
  };

  return (
    <OverviewContainer>
      <h3 style={{ marginBottom: '20px', color: '#2d3748', fontSize: '1.3rem', fontWeight: '600' }}>
        System Overview
      </h3>
      <MetricsGrid>
        <MetricCard $gradient="#667eea 0%, #764ba2 100%">
          <MetricValue>{formatNumber(getMetricValue('system_metrics.system.cpu.usage_percent'))}%</MetricValue>
          <MetricLabel>CPU Usage</MetricLabel>
        </MetricCard>
        
        <MetricCard $gradient="#f093fb 0%, #f5576c 100%">
          <MetricValue>{formatNumber(getMetricValue('system_metrics.system.memory.usage_percent'))}%</MetricValue>
          <MetricLabel>Memory Usage</MetricLabel>
        </MetricCard>
        
        <MetricCard $gradient="#4facfe 0%, #00f2fe 100%">
          <MetricValue>{formatNumber(getMetricValue('system_metrics.system.disk.usage_percent'))}%</MetricValue>
          <MetricLabel>Disk Usage</MetricLabel>
        </MetricCard>
        
        <MetricCard $gradient="#43e97b 0%, #38f9d7 100%">
          <MetricValue>{Math.floor(getMetricValue('application_metrics.logs_processed_total'))}</MetricValue>
          <MetricLabel>Logs Processed</MetricLabel>
        </MetricCard>
        
        <MetricCard $gradient="#fa709a 0%, #fee140 100%">
          <MetricValue>{Math.floor(getMetricValue('application_metrics.active_connections'))}</MetricValue>
          <MetricLabel>Active Connections</MetricLabel>
        </MetricCard>
        
        <MetricCard $gradient="#a8edea 0%, #fed6e3 100%">
          <MetricValue style={{color: '#2d3748'}}>{formatNumber(getMetricValue('application_metrics.error_rate'), 2)}%</MetricValue>
          <MetricLabel style={{color: '#4a5568'}}>Error Rate</MetricLabel>
        </MetricCard>
      </MetricsGrid>
    </OverviewContainer>
  );
};

export default SystemOverview;
