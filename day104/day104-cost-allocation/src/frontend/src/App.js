import React, { useState, useEffect, useRef } from 'react';
import { Layout, Menu, Card, Row, Col, Statistic, Table, Alert, Spin } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, BarChart, Bar, ResponsiveContainer } from 'recharts';
import { DollarOutlined, CloudOutlined, DatabaseOutlined, SearchOutlined, WarningOutlined } from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';
import './App.css';

const { Header, Content, Sider } = Layout;

const API_BASE_URL = 'http://localhost:8104';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function App() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [reports, setReports] = useState({});

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/dashboard/data`);
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const fetchDailyReport = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/reports/daily`);
      setReports(prev => ({ ...prev, daily: response.data }));
    } catch (error) {
      console.error('Error fetching daily report:', error);
    }
  };

  if (loading) {
    return (
      <Layout style={{ height: '100vh' }}>
        <Content style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  const tenantNames = dashboardData ? Object.keys(dashboardData.tenants) : [];
  
  const getTotalCosts = () => {
    if (!dashboardData) return 0;
    return Object.values(dashboardData.tenants).reduce((total, tenant) => {
      return total + (tenant.daily_cost?.total || 0);
    }, 0);
  };

  const getBudgetUtilization = () => {
    if (!dashboardData) return [];
    return Object.entries(dashboardData.tenants).map(([tenantId, data]) => ({
      tenant: tenantId,
      utilization: (data.daily_cost?.total || 0) / (data.budget_info?.budget_monthly || 1) * 30, // Estimate monthly
      budget: data.budget_info?.budget_monthly || 0,
      currentCost: data.daily_cost?.total || 0
    }));
  };

  const getResourceDistribution = () => {
    if (!dashboardData) return [];
    const resourceTotals = {};
    
    Object.values(dashboardData.tenants).forEach(tenant => {
      Object.entries(tenant.daily_cost || {}).forEach(([resource, cost]) => {
        if (resource !== 'total') {
          resourceTotals[resource] = (resourceTotals[resource] || 0) + cost;
        }
      });
    });
    
    return Object.entries(resourceTotals).map(([resource, cost]) => ({
      name: resource,
      value: cost
    }));
  };

  const getAlerts = () => {
    if (!dashboardData) return [];
    const alerts = [];
    
    Object.entries(dashboardData.tenants).forEach(([tenantId, data]) => {
      const utilization = (data.daily_cost?.total || 0) / (data.budget_info?.budget_monthly || 1) * 30;
      const threshold = data.budget_info?.alert_threshold || 0.9;
      
      if (utilization > threshold) {
        alerts.push({
          tenant: tenantId,
          type: 'budget',
          message: `${tenantId} is at ${(utilization * 100).toFixed(1)}% of monthly budget`,
          severity: utilization > 1.0 ? 'error' : 'warning'
        });
      }
    });
    
    return alerts;
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#1f1f1f', padding: '0 24px' }}>
        <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
          💰 Cost Allocation Dashboard
        </div>
      </Header>
      
      <Layout>
        <Sider width={250} style={{ background: '#fff', padding: '24px 0' }}>
          <Menu 
            mode="inline" 
            defaultSelectedKeys={['overview']}
            items={[
              {
                key: 'overview',
                icon: <DollarOutlined />,
                label: 'Cost Overview',
              },
              {
                key: 'tenants',
                icon: <CloudOutlined />,
                label: 'Tenant Details',
              },
              {
                key: 'reports',
                icon: <DatabaseOutlined />,
                label: 'Reports',
              },
            ]}
          />
        </Sider>
        
        <Content style={{ padding: '24px', background: '#f5f5f5' }}>
          {/* Alerts */}
          {getAlerts().length > 0 && (
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={24}>
                {getAlerts().map((alert, index) => (
                  <Alert
                    key={index}
                    message={alert.message}
                    type={alert.severity}
                    icon={<WarningOutlined />}
                    showIcon
                    style={{ marginBottom: 8 }}
                  />
                ))}
              </Col>
            </Row>
          )}
          
          {/* Key Metrics */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Daily Cost"
                  value={getTotalCosts()}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Active Tenants"
                  value={tenantNames.length}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Avg Cost/Tenant"
                  value={getTotalCosts() / Math.max(tenantNames.length, 1)}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Budget Alerts"
                  value={getAlerts().length}
                  valueStyle={{ color: getAlerts().length > 0 ? '#cf1322' : '#3f8600' }}
                />
              </Card>
            </Col>
          </Row>
          
          {/* Charts */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col span={12}>
              <Card title="Budget Utilization by Tenant">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getBudgetUtilization()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="tenant" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Utilization']} />
                    <Bar dataKey="utilization" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="Resource Cost Distribution">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={getResourceDistribution()}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={(entry) => `${entry.name}: $${entry.value.toFixed(2)}`}
                    >
                      {getResourceDistribution().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>
          
          {/* Tenant Details Table */}
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="Tenant Cost Details" extra={
                <span style={{ fontSize: '12px', color: '#666' }}>
                  Last updated: {moment(dashboardData?.timestamp).format('HH:mm:ss')}
                </span>
              }>
                <Table
                  dataSource={tenantNames.map(tenantId => {
                    const tenant = dashboardData.tenants[tenantId];
                    return {
                      key: tenantId,
                      tenant: tenantId,
                      dailyCost: tenant.daily_cost?.total || 0,
                      monthlyBudget: tenant.budget_info?.budget_monthly || 0,
                      utilization: ((tenant.daily_cost?.total || 0) / (tenant.budget_info?.budget_monthly || 1) * 30 * 100).toFixed(1),
                      ingestion: tenant.daily_cost?.ingestion || 0,
                      storage: tenant.daily_cost?.storage || 0,
                      queries: tenant.daily_cost?.queries || 0,
                      compute: tenant.daily_cost?.compute || 0
                    };
                  })}
                  columns={[
                    { title: 'Tenant', dataIndex: 'tenant', key: 'tenant' },
                    { 
                      title: 'Daily Cost', 
                      dataIndex: 'dailyCost', 
                      key: 'dailyCost',
                      render: (value) => `$${value.toFixed(2)}`
                    },
                    { 
                      title: 'Monthly Budget', 
                      dataIndex: 'monthlyBudget', 
                      key: 'monthlyBudget',
                      render: (value) => `$${value.toFixed(0)}`
                    },
                    { 
                      title: 'Utilization', 
                      dataIndex: 'utilization', 
                      key: 'utilization',
                      render: (value) => (
                        <span style={{ color: parseFloat(value) > 90 ? '#cf1322' : '#3f8600' }}>
                          {value}%
                        </span>
                      )
                    },
                    { 
                      title: 'Ingestion', 
                      dataIndex: 'ingestion', 
                      key: 'ingestion',
                      render: (value) => `$${value.toFixed(2)}`
                    },
                    { 
                      title: 'Storage', 
                      dataIndex: 'storage', 
                      key: 'storage',
                      render: (value) => `$${value.toFixed(2)}`
                    },
                    { 
                      title: 'Queries', 
                      dataIndex: 'queries', 
                      key: 'queries',
                      render: (value) => `$${value.toFixed(2)}`
                    },
                    { 
                      title: 'Compute', 
                      dataIndex: 'compute', 
                      key: 'compute',
                      render: (value) => `$${value.toFixed(2)}`
                    }
                  ]}
                  pagination={false}
                  size="small"
                />
              </Card>
            </Col>
          </Row>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
