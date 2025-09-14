import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Requirements from './pages/Requirements';
import TestGeneration from './pages/TestGeneration';
import BackgroundTasks from './pages/BackgroundTasks';
import DocumentUpload from './pages/DocumentUpload';
import JourneyManager from './components/JourneyManager';
import { ConfigProvider } from './contexts/ConfigContext';

// Create a modern banking/enterprise theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Professional blue
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e', // Accent red
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: '#2c3e50',
      secondary: '#7f8c8d',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      color: '#2c3e50',
    },
    h6: {
      fontWeight: 500,
      color: '#34495e',
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ConfigProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/requirements" element={<Requirements />} />
              <Route path="/test-generation" element={<TestGeneration />} />
              <Route path="/background-tasks" element={<BackgroundTasks />} />
              <Route path="/document-upload" element={<DocumentUpload />} />
              <Route path="/journey-management" element={<JourneyManager />} />
            </Routes>
          </Layout>
        </Router>
      </ConfigProvider>
    </ThemeProvider>
  );
}

export default App;
