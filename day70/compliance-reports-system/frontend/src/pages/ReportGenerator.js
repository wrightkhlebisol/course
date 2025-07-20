import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Alert,
  Card,
  CardContent,
  Chip,
  CircularProgress
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { generateReport, fetchFrameworks } from '../services/api';

function ReportGenerator() {
  const [frameworks, setFrameworks] = useState([]);
  const [formData, setFormData] = useState({
    framework: '',
    period_start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    period_end: new Date(),
    export_format: 'pdf',
    title: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadFrameworks();
  }, []);

  const loadFrameworks = async () => {
    try {
      const data = await fetchFrameworks();
      setFrameworks(data.frameworks);
    } catch (error) {
      console.error('Failed to load frameworks:', error);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!formData.framework) {
      setMessage({ type: 'error', text: 'Please select a compliance framework' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const response = await generateReport(formData);
      setMessage({
        type: 'success',
        text: `Report generation started! Report ID: ${response.report_id}`
      });
      
      // Reset form
      setFormData({
        ...formData,
        title: '',
        description: ''
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.message || 'Failed to generate report'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value
    });
  };

  const handleDateChange = (field) => (date) => {
    setFormData({
      ...formData,
      [field]: date
    });
  };

  const selectedFramework = frameworks.find(f => f.name === formData.framework);

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 500 }}>
        Generate Compliance Report
      </Typography>

      {message && (
        <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Report Configuration
            </Typography>
            
            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Compliance Framework</InputLabel>
                    <Select
                      value={formData.framework}
                      label="Compliance Framework"
                      onChange={handleInputChange('framework')}
                      required
                    >
                      {frameworks.map((framework) => (
                        <MenuItem key={framework.name} value={framework.name}>
                          {framework.name} - {framework.description}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Export Format</InputLabel>
                    <Select
                      value={formData.export_format}
                      label="Export Format"
                      onChange={handleInputChange('export_format')}
                    >
                      <MenuItem value="pdf">PDF Report</MenuItem>
                      <MenuItem value="csv">CSV Data</MenuItem>
                      <MenuItem value="json">JSON Data</MenuItem>
                      <MenuItem value="xml">XML Data</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <DatePicker
                      label="Period Start"
                      value={formData.period_start}
                      onChange={handleDateChange('period_start')}
                      renderInput={(params) => <TextField {...params} fullWidth />}
                    />
                  </LocalizationProvider>
                </Grid>

                <Grid item xs={12} md={6}>
                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <DatePicker
                      label="Period End"
                      value={formData.period_end}
                      onChange={handleDateChange('period_end')}
                      renderInput={(params) => <TextField {...params} fullWidth />}
                    />
                  </LocalizationProvider>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Report Title"
                    value={formData.title}
                    onChange={handleInputChange('title')}
                    placeholder="Optional custom title"
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Description"
                    value={formData.description}
                    onChange={handleInputChange('description')}
                    placeholder="Optional report description"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    disabled={loading}
                    sx={{ minWidth: 150 }}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Generate Report'}
                  </Button>
                </Grid>
              </Grid>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Framework Details
            </Typography>
            
            {selectedFramework ? (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {selectedFramework.description}
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Retention Period
                  </Typography>
                  <Chip 
                    label={`${selectedFramework.retention_days} days`}
                    color="primary"
                    variant="outlined"
                    size="small"
                  />
                </Box>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Required Data Fields
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {selectedFramework.required_fields.map((field) => (
                      <Chip 
                        key={field}
                        label={field.replace('_', ' ')}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Select a compliance framework to see details
              </Typography>
            )}
          </Paper>

          <Paper sx={{ p: 3, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Export Formats
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">PDF</Typography>
                <Typography variant="body2" color="text.secondary">
                  Formatted report
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">CSV</Typography>
                <Typography variant="body2" color="text.secondary">
                  Raw data
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">JSON</Typography>
                <Typography variant="body2" color="text.secondary">
                  Structured data
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">XML</Typography>
                <Typography variant="body2" color="text.secondary">
                  Legacy systems
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default ReportGenerator;
