import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Grid, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Box,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { 
  Notifications,
  Send,
  TrendingUp,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Info
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testSeverity, setTestSeverity] = useState('info');
  const [alertHistory, setAlertHistory] = useState([]);

  // Fetch statistics
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // Fetch recent notifications
  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/notifications/recent?limit=20`);
      setNotifications(response.data.notifications);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  // Fetch all data in parallel
  const fetchAllData = async () => {
    // Always clear loading state, even on error
    const clearLoading = () => {
      setInitialLoading(false);
    };
    
    try {
      const [statsResponse, notificationsResponse] = await Promise.all([
        axios.get(`${API_BASE}/api/stats`, { timeout: 5000 }),
        axios.get(`${API_BASE}/api/notifications/recent?limit=20`, { timeout: 5000 })
      ]);
      
      setStats(statsResponse.data);
      setNotifications(notificationsResponse.data.notifications);
      clearLoading();
    } catch (error) {
      console.error('Failed to fetch data:', error);
      // Set default values on error to prevent infinite loading
      setStats({
        current_rate_per_minute: 0,
        max_rate_per_minute: 60,
        recent_notifications: 0,
        queued_alerts: 0,
        deduplication_window_minutes: 5
      });
      setNotifications([]);
      clearLoading();
    }
  };

  // Send test alert
  const sendTestAlert = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/alerts/test?severity=${testSeverity}`);
      setAlertHistory(prev => [response.data, ...prev.slice(0, 9)]);
      setTestDialogOpen(false);
      
      // Refresh data in parallel
      setTimeout(() => {
        Promise.all([fetchStats(), fetchNotifications()]);
      }, 1000);
      
    } catch (error) {
      console.error('Failed to send test alert:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh data
  useEffect(() => {
    // Initial load - fetch in parallel
    fetchAllData();
    
    // Set up auto-refresh
    const interval = setInterval(() => {
      fetchStats();
      fetchNotifications();
    }, 10000); // Refresh every 10 seconds
    
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'error',
      error: 'warning', 
      warning: 'info',
      info: 'success'
    };
    return colors[severity] || 'default';
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      critical: <ErrorIcon />,
      error: <Warning />,
      warning: <Info />,
      info: <CheckCircle />
    };
    return icons[severity] || <Info />;
  };

  // Show loading state on initial load (with timeout fallback)
  useEffect(() => {
    // Safety timeout - if still loading after 15 seconds, force it to false
    const timeout = setTimeout(() => {
      if (initialLoading) {
        console.warn('Loading timeout - showing dashboard anyway');
        setInitialLoading(false);
      }
    }, 15000);
    
    return () => clearTimeout(timeout);
  }, [initialLoading]);

  if (initialLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            🔔 Slack Integration Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Real-time notifications for distributed log processing
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Box sx={{ textAlign: 'center' }}>
            <LinearProgress sx={{ width: '300px', mb: 2 }} />
            <Typography variant="body1" color="text.secondary">
              Loading dashboard...
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              If this takes too long, check your browser console for errors
            </Typography>
          </Box>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          🔔 Slack Integration Dashboard
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Real-time notifications for distributed log processing
        </Typography>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats?.current_rate_per_minute || 0}
                  </Typography>
                  <Typography variant="body2">
                    Alerts/Min
                  </Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
              {stats && (
                <LinearProgress 
                  variant="determinate" 
                  value={(stats.current_rate_per_minute / stats.max_rate_per_minute) * 100}
                  sx={{ mt: 2, bgcolor: 'rgba(255,255,255,0.2)' }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats?.recent_notifications || 0}
                  </Typography>
                  <Typography variant="body2">
                    Recent Notifications
                  </Typography>
                </Box>
                <Notifications sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats?.queued_alerts || 0}
                  </Typography>
                  <Typography variant="body2">
                    Queued Alerts
                  </Typography>
                </Box>
                <Warning sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats?.deduplication_window_minutes || 0}m
                  </Typography>
                  <Typography variant="body2">
                    Dedup Window
                  </Typography>
                </Box>
                <CheckCircle sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Controls */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Button 
              variant="contained" 
              startIcon={<Send />}
              onClick={() => setTestDialogOpen(true)}
              disabled={loading}
              sx={{ background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)' }}
            >
              Send Test Alert
            </Button>
            <Button 
              variant="outlined" 
              onClick={fetchStats}
              disabled={loading}
            >
              Refresh Stats
            </Button>
            {stats && (
              <Alert severity="info" sx={{ ml: 'auto' }}>
                Rate Limit: {stats.current_rate_per_minute}/{stats.max_rate_per_minute} per minute
              </Alert>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Recent Test Alerts */}
      {alertHistory.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              🧪 Recent Test Alerts
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Severity</TableCell>
                    <TableCell>Service</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Channel</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alertHistory.map((alert, index) => {
                  // Normalize status - handle both "failed" and "AlertStatus.FAILED"
                  const status = typeof alert.status.status === 'string' 
                    ? alert.status.status.replace('AlertStatus.', '').toLowerCase()
                    : alert.status.status;
                  const statusDisplay = status === 'sent' ? 'sent' : 
                                      status === 'failed' ? 'failed' : 
                                      status === 'pending' ? 'pending' : status;
                  
                  return (
                    <TableRow key={index}>
                      <TableCell>
                        <Chip 
                          icon={getSeverityIcon(alert.alert.severity)}
                          label={alert.alert.severity.toUpperCase()}
                          color={getSeverityColor(alert.alert.severity)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{alert.alert.service}</TableCell>
                      <TableCell>{alert.alert.title}</TableCell>
                      <TableCell>
                        <Chip 
                          label={statusDisplay}
                          color={statusDisplay === 'sent' ? 'success' : 
                                 statusDisplay === 'failed' ? 'error' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{alert.status.channel || 'N/A'}</TableCell>
                    </TableRow>
                  );
                })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Recent Notifications */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📋 Recent Notifications
          </Typography>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Alert ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Channel</TableCell>
                  <TableCell>Sent At</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {notifications.map((notification, index) => {
                  // Normalize status - handle both "failed" and "AlertStatus.FAILED"
                  const status = typeof notification.status === 'string'
                    ? notification.status.replace('AlertStatus.', '').toLowerCase()
                    : notification.status;
                  const statusDisplay = status === 'sent' ? 'sent' : 
                                      status === 'failed' ? 'failed' : 
                                      status === 'pending' ? 'pending' : status;
                  
                  return (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {notification.alert_id ? notification.alert_id.substring(0, 8) + '...' : 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={statusDisplay}
                          color={statusDisplay === 'sent' ? 'success' : 
                                 statusDisplay === 'failed' ? 'error' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{notification.channel || 'N/A'}</TableCell>
                      <TableCell>
                        {notification.sent_at && notification.sent_at.trim() ? 
                          new Date(notification.sent_at).toLocaleString() : 
                          statusDisplay === 'failed' ? 'Failed to send' :
                          statusDisplay === 'pending' ? 'Pending' :
                          'Not sent'
                        }
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Test Alert Dialog */}
      <Dialog 
        open={testDialogOpen} 
        onClose={() => setTestDialogOpen(false)}
        disableEnforceFocus
        aria-labelledby="test-alert-dialog-title"
      >
        <DialogTitle id="test-alert-dialog-title">Send Test Alert</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Severity</InputLabel>
            <Select
              value={testSeverity}
              onChange={(e) => setTestSeverity(e.target.value)}
              label="Severity"
            >
              <MenuItem value="info">Info</MenuItem>
              <MenuItem value="warning">Warning</MenuItem>
              <MenuItem value="error">Error</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button onClick={sendTestAlert} variant="contained" disabled={loading}>
            Send Alert
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default App;
