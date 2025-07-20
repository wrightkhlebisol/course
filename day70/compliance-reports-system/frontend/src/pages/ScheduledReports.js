import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { fetchScheduledReports, deleteScheduledReport } from '../services/api';

function ScheduledReports() {
  const [scheduledReports, setScheduledReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadScheduledReports();
  }, []);

  const loadScheduledReports = async () => {
    try {
      const data = await fetchScheduledReports();
      setScheduledReports(data.scheduled_reports || []);
      setError(null);
    } catch (err) {
      setError('Failed to load scheduled reports');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (scheduleId) => {
    try {
      await deleteScheduledReport(scheduleId);
      await loadScheduledReports();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 500 }}>
          Scheduled Reports
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {/* TODO: Add schedule dialog */}}
        >
          Schedule Report
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Framework</TableCell>
                <TableCell>Schedule</TableCell>
                <TableCell>Format</TableCell>
                <TableCell>Recipients</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {scheduledReports.map((schedule) => (
                <TableRow key={schedule.id} hover>
                  <TableCell>
                    <Chip label={schedule.framework} size="small" color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell>{schedule.schedule_type}</TableCell>
                  <TableCell>{schedule.export_format?.toUpperCase()}</TableCell>
                  <TableCell>{schedule.recipients?.length || 0} recipients</TableCell>
                  <TableCell>
                    <Chip 
                      label={schedule.enabled ? 'Active' : 'Inactive'} 
                      size="small" 
                      color={schedule.enabled ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton
                      onClick={() => handleDelete(schedule.id)}
                      size="small"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {scheduledReports.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} sx={{ textAlign: 'center', py: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      No scheduled reports configured
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}

export default ScheduledReports;
