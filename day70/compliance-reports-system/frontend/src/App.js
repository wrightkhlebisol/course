import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Tab,
  Tabs,
  Paper
} from '@mui/material';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ReportGenerator from './pages/ReportGenerator';
import ReportsList from './pages/ReportsList';
import ScheduledReports from './pages/ScheduledReports';
import './App.css';

// Google Cloud Skills Boost inspired theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Google Blue
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#ff9800', // Orange accent
      light: '#ffb74d',
      dark: '#f57c00',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
    }
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", "Arial", sans-serif',
    h4: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    }
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 20,
          textTransform: 'none',
          fontWeight: 500,
        }
      }
    }
  }
});

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`nav-tabpanel-${index}`}
      aria-labelledby={`nav-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function NavigationTabs() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const getTabValue = () => {
    switch (location.pathname) {
      case '/': return 0;
      case '/generate': return 1;
      case '/reports': return 2;
      case '/scheduled': return 3;
      default: return 0;
    }
  };

  const handleTabChange = (event, newValue) => {
    switch (newValue) {
      case 0: navigate('/'); break;
      case 1: navigate('/generate'); break;
      case 2: navigate('/reports'); break;
      case 3: navigate('/scheduled'); break;
      default: navigate('/');
    }
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      <Container maxWidth="lg">
        <Tabs
          value={getTabValue()}
          onChange={handleTabChange}
          aria-label="compliance reports navigation"
          sx={{
            '& .MuiTab-root': {
              minWidth: 0,
              px: 3,
              textTransform: 'none',
              fontWeight: 500,
            }
          }}
        >
          <Tab label="Dashboard" />
          <Tab label="Generate Report" />
          <Tab label="Reports" />
          <Tab label="Scheduled" />
        </Tabs>
      </Container>
    </Box>
  );
}

function AppContent() {
  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100vh' }}>
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 500 }}>
            Compliance Reports System
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            Day 70: Automated Compliance & Export
          </Typography>
        </Toolbar>
      </AppBar>
      
      <NavigationTabs />
      
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/generate" element={<ReportGenerator />} />
          <Route path="/reports" element={<ReportsList />} />
          <Route path="/scheduled" element={<ScheduledReports />} />
        </Routes>
      </Container>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
}

export default App;
