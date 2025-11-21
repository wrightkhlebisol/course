import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // Feature Flags
  getFlags: () => api.get('/flags').then(res => res.data),
  createFlag: (flagData) => api.post('/flags', flagData).then(res => res.data),
  updateFlag: ({ id, ...data }) => api.put(`/flags/${id}`, data).then(res => res.data),
  deleteFlag: (id) => api.delete(`/flags/${id}`).then(res => res.data),
  
  // Flag Evaluation
  evaluateFlag: (evaluation) => api.post('/flags/evaluate', evaluation).then(res => res.data),
  
  // Logs
  getFlagLogs: (flagName) => api.get(`/flags/${flagName}/logs`).then(res => res.data),
  getRecentLogs: () => api.get('/logs/recent').then(res => res.data),
};
