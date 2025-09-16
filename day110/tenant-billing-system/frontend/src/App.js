import React, { useState, useEffect } from 'react';
import { Layout, Menu, Card, Row, Col, Statistic, Table, Select, Button, Progress } from 'antd';
import { 
  DashboardOutlined, 
  FileTextOutlined, 
  SettingOutlined, 
  DollarCircleOutlined,
  CloudServerOutlined,
  BarChartOutlined 
} from '@ant-design/icons';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Option } = Select;

const API_BASE = 'http://localhost:8000';

function App() {
  const [loading, setLoading] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState('tenant_1');
  const [tenants, setTenants] = useState([]);
  const [overview, setOverview] = useState(null);
  const [currentUsage, setCurrentUsage] = useState({});
  const [billing, setBilling] = useState({});
  const [quotaStatus, setQuotaStatus] = useState({});
  const [selectedMenu, setSelectedMenu] = useState('dashboard');

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch all data in parallel
      const [tenantsRes, overviewRes, usageRes, billingRes, quotaRes] = await Promise.all([
        axios.get(`${API_BASE}/tenants`),
        axios.get(`${API_BASE}/dashboard/overview`),
        axios.get(`${API_BASE}/usage/${selectedTenant}/current`),
        axios.get(`${API_BASE}/usage/${selectedTenant}/billing`),
        axios.get(`${API_BASE}/usage/${selectedTenant}/quota`)
      ]);

      setTenants(tenantsRes.data);
      setOverview(overviewRes.data);
      setCurrentUsage(usageRes.data);
      setBilling(billingRes.data);
      setQuotaStatus(quotaRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [selectedTenant]);

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const getTierColor = (tier) => {
    switch(tier) {
      case 'starter': return '#52c41a';
      case 'professional': return '#1890ff';
      case 'enterprise': return '#722ed1';
      default: return '#666';
    }
  };

  const getQuotaColor = (percentage) => {
    if (percentage < 70) return '#52c41a';
    if (percentage < 90) return '#faad14';
    return '#f5222d';
  };

  const renderDashboard = () => (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Monthly Cost"
              value={billing.total_cost}
              precision={2}
              prefix={<DollarCircleOutlined />}
              formatter={(value) => formatCurrency(value)}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Data Ingested Today"
              value={currentUsage.daily_bytes_ingested}
              formatter={(value) => formatBytes(value)}
              prefix={<CloudServerOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Storage Used"
              value={currentUsage.current_storage_used}
              formatter={(value) => formatBytes(value)}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Daily Queries"
              value={currentUsage.daily_queries_processed || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="Cost Breakdown" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  dataKey="value"
                  data={[
                    { name: 'Ingestion', value: billing.ingestion_cost || 0 },
                    { name: 'Storage', value: billing.storage_cost || 0 },
                    { name: 'Queries', value: billing.query_cost || 0 },
                    { name: 'Compute', value: billing.compute_cost || 0 },
                    { name: 'Bandwidth', value: billing.bandwidth_cost || 0 }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                >
                  {['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'].map((color, index) => (
                    <Cell key={`cell-${index}`} fill={color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Quota Usage" style={{ height: 400 }}>
            <div style={{ padding: 20 }}>
              <div style={{ marginBottom: 24 }}>
                <div>Daily Ingestion Quota</div>
                <Progress
                  percent={quotaStatus.current_usage ? 
                    (quotaStatus.current_usage.daily_bytes_ingested / quotaStatus.daily_ingestion_limit * 100) : 0}
                  strokeColor={getQuotaColor(quotaStatus.current_usage ? 
                    (quotaStatus.current_usage.daily_bytes_ingested / quotaStatus.daily_ingestion_limit * 100) : 0)}
                />
              </div>
              <div style={{ marginBottom: 24 }}>
                <div>Storage Quota</div>
                <Progress
                  percent={quotaStatus.current_usage ? 
                    (quotaStatus.current_usage.current_storage_used / quotaStatus.storage_limit * 100) : 0}
                  strokeColor={getQuotaColor(quotaStatus.current_usage ? 
                    (quotaStatus.current_usage.current_storage_used / quotaStatus.storage_limit * 100) : 0)}
                />
              </div>
              <div>
                <div>Daily Query Quota</div>
                <Progress
                  percent={quotaStatus.current_usage ? 
                    (quotaStatus.current_usage.daily_queries_processed / quotaStatus.query_limit * 100) : 0}
                  strokeColor={getQuotaColor(quotaStatus.current_usage ? 
                    (quotaStatus.current_usage.daily_queries_processed / quotaStatus.query_limit * 100) : 0)}
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="All Tenants Overview">
        <Table
          dataSource={overview?.tenants || []}
          rowKey="tenant_id"
          columns={[
            {
              title: 'Tenant',
              dataIndex: 'name',
              key: 'name',
            },
            {
              title: 'Tier',
              dataIndex: 'tier',
              key: 'tier',
              render: (tier) => (
                <span style={{ color: getTierColor(tier) }}>
                  {tier.toUpperCase()}
                </span>
              ),
            },
            {
              title: 'Daily Data (GB)',
              dataIndex: 'daily_bytes_gb',
              key: 'daily_bytes_gb',
              render: (value) => value.toFixed(4),
            },
            {
              title: 'Monthly Cost',
              dataIndex: 'monthly_cost',
              key: 'monthly_cost',
              render: (value) => formatCurrency(value),
            },
            {
              title: 'Storage (GB)',
              dataIndex: 'storage_gb',
              key: 'storage_gb',
              render: (value) => value.toFixed(2),
            },
            {
              title: 'Daily Queries',
              dataIndex: 'daily_queries',
              key: 'daily_queries',
            },
          ]}
        />
      </Card>
    </div>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} className="site-layout-background">
        <div className="logo" style={{ padding: '16px', color: 'white', fontWeight: 'bold' }}>
          Billing Dashboard
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedMenu]}
          style={{ height: '100%', borderRight: 0 }}
          onClick={({ key }) => setSelectedMenu(key)}
          items={[
            {
              key: 'dashboard',
              icon: <DashboardOutlined />,
              label: 'Dashboard',
            },
            {
              key: 'reports',
              icon: <FileTextOutlined />,
              label: 'Reports',
            },
            {
              key: 'settings',
              icon: <SettingOutlined />,
              label: 'Settings',
            },
          ]}
        />
      </Sider>
      <Layout>
        <Header className="site-layout-background" style={{ padding: 0, background: '#fff' }}>
          <div style={{ padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h1>Usage Reporting & Billing System</h1>
            <div>
              <Select
                style={{ width: 200, marginRight: 16 }}
                placeholder="Select Tenant"
                value={selectedTenant}
                onChange={setSelectedTenant}
              >
                {tenants.map(tenant => (
                  <Option key={tenant.id} value={tenant.id}>
                    {tenant.name} ({tenant.tier})
                  </Option>
                ))}
              </Select>
              <Button onClick={fetchData} loading={loading}>
                Refresh
              </Button>
            </div>
          </div>
        </Header>
        <Content style={{ margin: '0 16px' }}>
          <div style={{ padding: 24, minHeight: 360 }}>
            {selectedMenu === 'dashboard' && renderDashboard()}
            {selectedMenu === 'reports' && (
              <Card>
                <h2>Reports will be available in the next release</h2>
              </Card>
            )}
            {selectedMenu === 'settings' && (
              <Card>
                <h2>Settings will be available in the next release</h2>
              </Card>
            )}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
