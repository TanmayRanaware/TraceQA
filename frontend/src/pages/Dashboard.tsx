import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';

import {
  Dashboard as DashboardIcon,
  Upload,
  Search,
  BugReport,
  Schedule,
  Storage,
  Memory,
  Cloud,
} from '@mui/icons-material';
import axios from 'axios';
import { useConfig } from '../contexts/ConfigContext';

interface VectorDBStats {
  status: string;
  storage_type: string;
  vector_count: number;
  stats?: {
    total_vector_count: number;
    dimension: number;
    index_fullness: number;
    namespaces: any;
  };
}

const Dashboard: React.FC = () => {
  const { config } = useConfig();
  const [providerInfo, setProviderInfo] = useState<any>(null);
  const [backgroundTasks, setBackgroundTasks] = useState<any[]>([]);
  const [vectorDBStats, setVectorDBStats] = useState<VectorDBStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch provider info
      const providerResponse = await axios.get('/requirements/provider-info');
      setProviderInfo(providerResponse.data);
      
      // Fetch background tasks
      const tasksResponse = await axios.get('/background/tasks');
      setBackgroundTasks(tasksResponse.data.tasks || []);
      
      // Fetch vector DB stats
      try {
        const vectorDBResponse = await axios.get('/api/vector-db/health');
        setVectorDBStats(vectorDBResponse.data);
      } catch (vectorDBError) {
        console.warn('Vector DB stats not available:', vectorDBError);
        setVectorDBStats({
          status: 'unavailable',
          storage_type: 'unknown',
          vector_count: 0
        });
      }
      
    } catch (err) {
      setError('Failed to fetch dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStorageIcon = (storageType: string | undefined) => {
    if (!storageType) {
      return <Storage color="action" />;
    }
    switch (storageType.toLowerCase()) {
      case 'pinecone':
        return <Cloud color="primary" />;
      case 'memory':
        return <Memory color="secondary" />;
      default:
        return <Storage color="action" />;
    }
  };

  const getStorageColor = (storageType: string | undefined) => {
    if (!storageType) {
      return 'default';
    }
    switch (storageType.toLowerCase()) {
      case 'pinecone':
        return 'success';
      case 'memory':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (!config) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Loading configuration...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <DashboardIcon color="primary" />
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {/* System Overview */}
        <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Storage color="primary" />
                System Overview
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  LLM Provider
                </Typography>
                <Chip
                  label={providerInfo?.provider_type || 'Unknown'}
                  color={providerInfo?.is_claude ? 'success' : providerInfo?.is_gemini ? 'primary' : 'default'}
                  size="small"
                />
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Vector Database
                </Typography>
                {vectorDBStats ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStorageIcon(vectorDBStats.storage_type)}
                    <Chip
                      label={vectorDBStats.storage_type || 'Unknown'}
                      color={getStorageColor(vectorDBStats.storage_type) as any}
                      size="small"
                    />
                    <Typography variant="body2" color="text.secondary">
                      ({vectorDBStats.vector_count || 0} vectors)
                    </Typography>
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Loading...
                  </Typography>
                )}
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Configuration
                </Typography>
                <Typography variant="body2">
                  • {config.journeys.length} Journeys configured
                </Typography>
                <Typography variant="body2">
                  • {config.source_types.length} Source types supported
                </Typography>
                <Typography variant="body2">
                  • {config.supported_formats.length} File formats supported
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Quick Actions */}
        <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Upload color="primary" />
                Quick Actions
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<Upload />}
                  fullWidth
                  href="/document-upload"
                >
                  Upload Requirements
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Search />}
                  fullWidth
                  href="/requirements"
                >
                  Search Requirements
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<BugReport />}
                  fullWidth
                  href="/test-generation"
                >
                  Generate Tests
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Schedule />}
                  fullWidth
                  href="/background-tasks"
                >
                  Monitor Tasks
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Vector Database Statistics */}
        <Box sx={{ flex: '1 1 100%', minWidth: '100%' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Cloud color="primary" />
                Vector Database Statistics
              </Typography>
              
              {vectorDBStats ? (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {vectorDBStats.vector_count || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Vectors
                      </Typography>
                    </Paper>
                  </Box>
                  
                  <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="secondary">
                        {vectorDBStats.stats?.dimension || 768}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Vector Dimension
                      </Typography>
                    </Paper>
                  </Box>
                  
                  <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="success">
                        {vectorDBStats.storage_type || 'Unknown'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Storage Type
                      </Typography>
                    </Paper>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <CircularProgress size={40} />
                  <Typography sx={{ mt: 2 }}>Loading vector database stats...</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Recent Activity */}
        <Box sx={{ flex: '1 1 100%', minWidth: '100%' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Schedule color="primary" />
                Recent Activity
              </Typography>
              
              {backgroundTasks.length > 0 ? (
                <List>
                  {backgroundTasks.slice(0, 5).map((task, index) => (
                    <React.Fragment key={task.id || index}>
                      <ListItem>
                        <ListItemIcon>
                          <Schedule color="action" />
                        </ListItemIcon>
                        <ListItemText
                          primary={task.task_type || 'Unknown Task'}
                          secondary={`Status: ${task.status} | Created: ${new Date(task.created_at).toLocaleString()}`}
                        />
                        <Chip
                          label={task.status}
                          color={task.status === 'completed' ? 'success' : 'warning'}
                          size="small"
                        />
                      </ListItem>
                      {index < backgroundTasks.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Typography color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  No recent activity
                </Typography>
              )}
            </CardContent>
          </Card>
        </Box>
                        </Box>
    </Box>
  );
};

export default Dashboard;
