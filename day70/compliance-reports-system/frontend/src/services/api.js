import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Add request interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    throw error;
  }
);

export const fetchDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

export const fetchFrameworks = async () => {
  const response = await api.get('/frameworks');
  return response.data;
};

export const generateReport = async (reportData) => {
  const response = await api.post('/reports/generate', reportData);
  return response.data;
};

export const fetchReports = async () => {
  const response = await api.get('/reports');
  return response.data;
};

export const fetchReport = async (reportId) => {
  const response = await api.get(`/reports/${reportId}`);
  return response.data;
};

export const downloadReport = async (reportId) => {
  const response = await api.get(`/reports/${reportId}/download`, {
    responseType: 'blob',
  });
  return response.data;
};

export const scheduleReport = async (scheduleData) => {
  const response = await api.post('/reports/schedule', scheduleData);
  return response.data;
};

export const fetchScheduledReports = async () => {
  const response = await api.get('/reports/schedule');
  return response.data;
};

export const deleteScheduledReport = async (scheduleId) => {
  await api.delete(`/reports/schedule/${scheduleId}`);
};

export default api;
