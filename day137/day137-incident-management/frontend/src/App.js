import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  AlertTitle,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import { 
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Notifications as NotificationsIcon 
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [healthStatus, setHealthStatus] = useState({});
  const [metrics, setMetrics] = useState({});
  const [incidents, setIncidents] = useState([]);
  const [alertDialogOpen, setAlertDialogOpen] = useState(false);
  const [newAlert, setNewAlert] = useState({
    title: '',
    description: '',
    source: 'application',
    severity: 'medium',
    service_name: '',
    tags: ''
  });

  useEffect(() => {
    fetchHealthStatus();
    fetchMetrics();
    fetchIncidents();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      fetchHealthStatus();
      fetchMetrics();
      fetchIncidents();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Fix aria-hidden issue: Remove aria-hidden from root when dialog is open
  useEffect(() => {
    const rootElement = document.getElementById('root');
    if (alertDialogOpen && rootElement) {
      // Aggressively remove aria-hidden to fix accessibility issue
      const removeAriaHidden = () => {
        if (rootElement.getAttribute('aria-hidden') === 'true') {
          rootElement.removeAttribute('aria-hidden');
        }
      };
      
      // Use MutationObserver for attribute changes
      const observer = new MutationObserver(removeAriaHidden);
      observer.observe(rootElement, {
        attributes: true,
        attributeFilter: ['aria-hidden'],
        subtree: false
      });
      
      // Also use interval as backup to catch any missed changes
      const interval = setInterval(removeAriaHidden, 100);
      
      // Initial check
      removeAriaHidden();
      
      return () => {
        observer.disconnect();
        clearInterval(interval);
      };
    }
  }, [alertDialogOpen]);

  const fetchHealthStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`);
      console.log('Health Status:', response.data);
      setHealthStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch health status:', error);
      setHealthStatus({ system_status: 'unknown', active_incidents: 0 });
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/metrics`);
      console.log('Metrics:', response.data);
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      setMetrics({ alerts_processed: 0, api_errors: {}, average_response_times: {} });
    }
  };

  const fetchIncidents = async () => {
    try {
      const response = await axios.get(`${API_BASE}/incidents`);
      console.log('Incidents Response:', response.data);
      // Combine incidents from all providers
      const allIncidents = [
        ...(response.data.pagerduty || []).map(i => ({...i, provider: 'PagerDuty'})),
        ...(response.data.opsgenie || []).map(i => ({...i, provider: 'OpsGenie'})),
        ...(response.data.local_incidents || []).map(i => ({...i, provider: 'Local'}))
      ];
      console.log('All Incidents:', allIncidents);
      setIncidents(allIncidents);
    } catch (error) {
      console.error('Failed to fetch incidents:', error);
      setIncidents([]);
    }
  };

  const handleCreateAlert = async () => {
    try {
      const alertData = {
        ...newAlert,
        tags: newAlert.tags.split(',').map(t => t.trim()).filter(t => t),
        timestamp: new Date().toISOString()
      };
      
      console.log('Creating alert:', alertData);
      const response = await axios.post(`${API_BASE}/alerts`, alertData);
      console.log('Alert created:', response.data);
      
      setAlertDialogOpen(false);
      setNewAlert({
        title: '',
        description: '',
        source: 'application',
        severity: 'medium',
        service_name: '',
        tags: ''
      });
      
      // Refresh data after a short delay to ensure backend has processed
      setTimeout(() => {
        fetchIncidents();
        fetchMetrics();
        fetchHealthStatus();
      }, 500);
    } catch (error) {
      console.error('Failed to create alert:', error);
      alert('Failed to create alert: ' + (error.response?.data?.error || error.message));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'operational': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#c41e3a';
      case 'high': return '#ff8c00';
      case 'medium': return '#ffa500';
      case 'low': return '#4a7c2a';
      default: return '#6c757d';
    }
  };

  // Mock chart data
  const chartData = [
    { time: '00:00', alerts: 12, incidents: 2 },
    { time: '04:00', alerts: 8, incidents: 1 },
    { time: '08:00', alerts: 25, incidents: 4 },
    { time: '12:00', alerts: 18, incidents: 3 },
    { time: '16:00', alerts: 32, incidents: 6 },
    { time: '20:00', alerts: 15, incidents: 2 }
  ];

  const severityData = [
    { name: 'Critical', value: 5, color: '#ef4444' },
    { name: 'High', value: 12, color: '#f59e0b' },
    { name: 'Medium', value: 23, color: '#fbbf24' },
    { name: 'Low', value: 15, color: '#10b981' }
  ];

  return (
    <div className="App">
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h3" gutterBottom sx={{ mb: 4, fontWeight: 'bold', color: '#f1f5f9', textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)' }}>
          🚨 Incident Management Dashboard
        </Typography>

        {/* System Health Status */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card className="colored-card" sx={{ background: 'linear-gradient(135deg, #0d9488 0%, #14b8a6 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <CheckIcon sx={{ mr: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>System Status</Typography>
                </Box>
                <Typography variant="h4" sx={{ mt: 1, fontWeight: 700 }}>
                  {healthStatus.system_status || 'Unknown'}
                </Typography>
                <Chip 
                  label={healthStatus.system_status || 'Unknown'} 
                  color={getStatusColor(healthStatus.system_status)}
                  sx={{ mt: 1, backgroundColor: 'rgba(255, 255, 255, 0.2)', color: 'white' }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card className="colored-card" sx={{ background: 'linear-gradient(135deg, #d97706 0%, #f59e0b 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <NotificationsIcon sx={{ mr: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>Active Incidents</Typography>
                </Box>
                <Typography variant="h4" sx={{ mt: 1, fontWeight: 700 }}>
                  {healthStatus.active_incidents || 0}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, opacity: 0.95 }}>
                  Across all providers
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card className="colored-card" sx={{ background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <WarningIcon sx={{ mr: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>Alerts Processed</Typography>
                </Box>
                <Typography variant="h4" sx={{ mt: 1, fontWeight: 700 }}>
                  {metrics.alerts_processed || 0}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, opacity: 0.95 }}>
                  Total processed today
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card className="colored-card" sx={{ background: 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)' }}>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <ErrorIcon sx={{ mr: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>API Errors</Typography>
                </Box>
                <Typography variant="h4" sx={{ mt: 1, fontWeight: 700 }}>
                  {Object.values(metrics.api_errors || {}).reduce((a, b) => a + b, 0)}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, opacity: 0.95 }}>
                  Across all providers
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Integration Health */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2, boxShadow: 3, backgroundColor: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.1)' }}>
              <Typography variant="h6" gutterBottom sx={{ color: '#f1f5f9' }}>Integration Health</Typography>
              <Box sx={{ mt: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                  <Typography variant="body1" sx={{ color: '#e2e8f0' }}>PagerDuty</Typography>
                  <Chip 
                    label={
                      healthStatus.integration_status?.pagerduty?.configured === false 
                        ? 'Active' 
                        : (healthStatus.uptime_checks?.pagerduty ? 'Healthy' : 'Down')
                    } 
                    color={
                      healthStatus.integration_status?.pagerduty?.configured === false
                        ? 'success'
                        : (healthStatus.uptime_checks?.pagerduty ? 'success' : 'error')
                    }
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body1" sx={{ color: '#e2e8f0' }}>OpsGenie</Typography>
                  <Chip 
                    label={
                      healthStatus.integration_status?.opsgenie?.configured === false 
                        ? 'Active' 
                        : (healthStatus.uptime_checks?.opsgenie ? 'Healthy' : 'Down')
                    } 
                    color={
                      healthStatus.integration_status?.opsgenie?.configured === false
                        ? 'success'
                        : (healthStatus.uptime_checks?.opsgenie ? 'success' : 'error')
                    }
                  />
                </Box>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, borderRadius: 2, boxShadow: 3, backgroundColor: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.1)' }}>
              <Typography variant="h6" gutterBottom sx={{ color: '#f1f5f9' }}>Response Times</Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" sx={{ color: '#cbd5e1' }}>
                  PagerDuty: {metrics.average_response_times?.pagerduty_avg_ms?.toFixed(1) || 0}ms
                </Typography>
                <Typography variant="body2" sx={{ color: '#cbd5e1' }}>
                  OpsGenie: {metrics.average_response_times?.opsgenie_avg_ms?.toFixed(1) || 0}ms
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Charts */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3, borderRadius: 2, boxShadow: 3, backgroundColor: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.1)' }}>
              <Typography variant="h6" gutterBottom sx={{ color: '#f1f5f9' }}>Alert & Incident Trends</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#cbd5e1" />
                  <YAxis stroke="#cbd5e1" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#f1f5f9' }} />
                  <Line type="monotone" dataKey="alerts" stroke="#14b8a6" strokeWidth={2} />
                  <Line type="monotone" dataKey="incidents" stroke="#ef4444" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, borderRadius: 2, boxShadow: 3, backgroundColor: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.1)' }}>
              <Typography variant="h6" gutterBottom sx={{ color: '#f1f5f9' }}>Alert Severity Distribution</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#f1f5f9' }} />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>

        {/* Create Alert Button */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Button 
            variant="contained" 
            color="primary" 
            size="large"
            onClick={() => setAlertDialogOpen(true)}
            sx={{ borderRadius: 3, px: 4 }}
          >
            🚨 Create Test Alert
          </Button>
        </Box>

        {/* Recent Incidents Table */}
        <Paper sx={{ p: 3, borderRadius: 2, boxShadow: 3, backgroundColor: '#1e293b', border: '1px solid rgba(148, 163, 184, 0.1)' }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#f1f5f9' }}>Recent Incidents</Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Provider</strong></TableCell>
                  <TableCell><strong>Title</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Created</strong></TableCell>
                  <TableCell><strong>Service</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {incidents.slice(0, 10).map((incident, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Chip 
                        label={incident.provider} 
                        size="small"
                        color={incident.provider === 'PagerDuty' ? 'primary' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell sx={{ color: '#e2e8f0' }}>{incident.title || incident.message || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip 
                        label={incident.status || 'unknown'} 
                        size="small"
                        color={incident.status === 'resolved' ? 'success' : 'warning'}
                      />
                    </TableCell>
                    <TableCell sx={{ color: '#e2e8f0' }}>{incident.created_at || incident.createdAt || 'N/A'}</TableCell>
                    <TableCell sx={{ color: '#e2e8f0' }}>{incident.service?.summary || incident.entity || 'N/A'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Create Alert Dialog */}
        <Dialog 
          open={alertDialogOpen} 
          onClose={() => setAlertDialogOpen(false)} 
          maxWidth="md" 
          fullWidth
          disableEnforceFocus={true}
          disableAutoFocus={false}
          aria-labelledby="alert-dialog-title"
          aria-describedby="alert-dialog-description"
        >
          <DialogTitle id="alert-dialog-title">Create Test Alert</DialogTitle>
          <DialogContent id="alert-dialog-description">
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Alert Title"
                  value={newAlert.title}
                  onChange={(e) => setNewAlert({...newAlert, title: e.target.value})}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Description"
                  value={newAlert.description}
                  onChange={(e) => setNewAlert({...newAlert, description: e.target.value})}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Source</InputLabel>
                  <Select
                    value={newAlert.source}
                    onChange={(e) => setNewAlert({...newAlert, source: e.target.value})}
                  >
                    <MenuItem value="database">Database</MenuItem>
                    <MenuItem value="api">API</MenuItem>
                    <MenuItem value="security">Security</MenuItem>
                    <MenuItem value="infrastructure">Infrastructure</MenuItem>
                    <MenuItem value="application">Application</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Severity</InputLabel>
                  <Select
                    value={newAlert.severity}
                    onChange={(e) => setNewAlert({...newAlert, severity: e.target.value})}
                  >
                    <MenuItem value="critical">Critical</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="info">Info</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Service Name"
                  value={newAlert.service_name}
                  onChange={(e) => setNewAlert({...newAlert, service_name: e.target.value})}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Tags (comma separated)"
                  value={newAlert.tags}
                  onChange={(e) => setNewAlert({...newAlert, tags: e.target.value})}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAlertDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleCreateAlert}
              size="large"
            >
              Create Alert
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </div>
  );
}

export default App;
