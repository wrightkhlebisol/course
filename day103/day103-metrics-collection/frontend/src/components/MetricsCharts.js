import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import styled from 'styled-components';

const ChartContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
`;

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
`;

const ChartTitle = styled.h3`
  color: #2d3748;
  margin-bottom: 16px;
  font-size: 1.2rem;
  font-weight: 600;
`;

const MetricsCharts = ({ metricsData }) => {
  const [historicalData, setHistoricalData] = useState({
    cpu: [],
    memory: [],
    disk: [],
    timestamps: []
  });

  useEffect(() => {
    if (metricsData && metricsData.system_metrics) {
      const timestamp = new Date().toLocaleTimeString();
      
      setHistoricalData(prev => {
        const maxPoints = 50;
        const newData = {
          cpu: [...prev.cpu, metricsData.system_metrics['system.cpu.usage_percent'] || 0].slice(-maxPoints),
          memory: [...prev.memory, metricsData.system_metrics['system.memory.usage_percent'] || 0].slice(-maxPoints),
          disk: [...prev.disk, metricsData.system_metrics['system.disk.usage_percent'] || 0].slice(-maxPoints),
          timestamps: [...prev.timestamps, timestamp].slice(-maxPoints)
        };
        return newData;
      });
    }
  }, [metricsData]);

  const plotConfig = {
    displayModeBar: false,
    responsive: true
  };

  const plotLayout = {
    autosize: true,
    margin: { l: 50, r: 20, t: 20, b: 40 },
    plot_bgcolor: 'rgba(0,0,0,0)',
    paper_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Arial, sans-serif', size: 12, color: '#2d3748' },
    xaxis: { 
      showgrid: true, 
      gridcolor: 'rgba(0,0,0,0.1)',
      showline: true,
      linecolor: 'rgba(0,0,0,0.2)'
    },
    yaxis: { 
      showgrid: true, 
      gridcolor: 'rgba(0,0,0,0.1)',
      showline: true,
      linecolor: 'rgba(0,0,0,0.2)',
      range: [0, 100]
    }
  };

  return (
    <ChartContainer>
      <ChartTitle>System Performance Metrics</ChartTitle>
      <ChartGrid>
        <div>
          <h4 style={{ marginBottom: '12px', color: '#4a5568' }}>CPU Usage (%)</h4>
          <Plot
            data={[{
              x: historicalData.timestamps,
              y: historicalData.cpu,
              type: 'scatter',
              mode: 'lines+markers',
              line: { color: '#e53e3e', width: 2 },
              marker: { size: 4, color: '#e53e3e' },
              fill: 'tonexty',
              fillcolor: 'rgba(229, 62, 62, 0.1)'
            }]}
            layout={plotLayout}
            config={plotConfig}
            style={{ width: '100%', height: '300px' }}
          />
        </div>
        
        <div>
          <h4 style={{ marginBottom: '12px', color: '#4a5568' }}>Memory Usage (%)</h4>
          <Plot
            data={[{
              x: historicalData.timestamps,
              y: historicalData.memory,
              type: 'scatter',
              mode: 'lines+markers',
              line: { color: '#3182ce', width: 2 },
              marker: { size: 4, color: '#3182ce' },
              fill: 'tonexty',
              fillcolor: 'rgba(49, 130, 206, 0.1)'
            }]}
            layout={plotLayout}
            config={plotConfig}
            style={{ width: '100%', height: '300px' }}
          />
        </div>
        
        <div>
          <h4 style={{ marginBottom: '12px', color: '#4a5568' }}>Disk Usage (%)</h4>
          <Plot
            data={[{
              x: historicalData.timestamps,
              y: historicalData.disk,
              type: 'scatter',
              mode: 'lines+markers',
              line: { color: '#38a169', width: 2 },
              marker: { size: 4, color: '#38a169' },
              fill: 'tonexty',
              fillcolor: 'rgba(56, 161, 105, 0.1)'
            }]}
            layout={plotLayout}
            config={plotConfig}
            style={{ width: '100%', height: '300px' }}
          />
        </div>
        
        <div>
          <h4 style={{ marginBottom: '12px', color: '#4a5568' }}>Application Metrics</h4>
          {metricsData && metricsData.application_metrics && (
            <div style={{ padding: '20px 0' }}>
              <div style={{ marginBottom: '12px' }}>
                <strong>Logs Processed:</strong> {metricsData.application_metrics.logs_processed_total || 0}
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong>Active Connections:</strong> {metricsData.application_metrics.active_connections || 0}
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong>Queue Depth:</strong> {metricsData.application_metrics.queue_depth || 0}
              </div>
              <div>
                <strong>Error Rate:</strong> {(metricsData.application_metrics.error_rate || 0).toFixed(2)}%
              </div>
            </div>
          )}
        </div>
      </ChartGrid>
    </ChartContainer>
  );
};

export default MetricsCharts;
