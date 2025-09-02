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
  LinearProgress,
  Alert,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Schedule,
  CheckCircle,
  Error,
  PlayArrow,
  Stop,
  Refresh,
  Delete,
  Warning,
} from '@mui/icons-material';
import axios from 'axios';

interface BackgroundTask {
  task_id: string;
  type: string;
  status: string;
  started_at: string;
  progress: number;
  result?: any;
  error?: string;
}

const BackgroundTasks: React.FC = () => {
  const [tasks, setTasks] = useState<BackgroundTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get('/background/tasks');
      setTasks(response.data.tasks || []);
    } catch (err) {
      setError('Failed to fetch tasks');
      console.error('Tasks fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await axios.delete(`/background/tasks/${taskId}`);
      fetchTasks(); // Refresh the list
    } catch (err) {
      setError('Failed to cancel task');
      console.error('Cancel task error:', err);
    }
  };

  const handleCleanup = async () => {
    try {
      await axios.post('/background/cleanup-completed');
      fetchTasks(); // Refresh the list
    } catch (err) {
      setError('Failed to cleanup tasks');
      console.error('Cleanup error:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <PlayArrow />;
      case 'completed': return <CheckCircle />;
      case 'failed': return <Error />;
      case 'cancelled': return <Stop />;
      default: return <Schedule />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(parseInt(timestamp) * 1000);
    return date.toLocaleString();
  };

  const getTaskTypeLabel = (type: string) => {
    switch (type) {
      case 'batch_test_generation': return 'Batch Test Generation';
      case 'document_cleanup': return 'Document Cleanup';
      case 'impact_analysis': return 'Impact Analysis';
      default: return type;
    }
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" sx={{ mb: 1, fontWeight: 700 }}>
          Background Tasks
        </Typography>
        <Typography variant="h6" sx={{ color: 'text.secondary' }}>
          Monitor and manage long-running background operations
        </Typography>
      </Box>

      {/* Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2, alignItems: 'center' }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Task Management
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {tasks.length} total tasks • {tasks.filter(t => t.status === 'running').length} running
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                onClick={fetchTasks}
                startIcon={<Refresh />}
              >
                Refresh
              </Button>
              <Button
                variant="outlined"
                onClick={handleCleanup}
                color="warning"
              >
                Cleanup Completed
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tasks List */}
      {tasks.length > 0 ? (
        <List>
          {tasks.map((task, index) => (
            <React.Fragment key={task.task_id}>
              <ListItem sx={{ px: 0, py: 2 }}>
                <ListItemIcon>
                  {getStatusIcon(task.status)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Typography variant="h6">
                        {getTaskTypeLabel(task.type)}
                      </Typography>
                      <Chip
                        label={task.status}
                        color={getStatusColor(task.status) as any}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        ID: {task.task_id}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Started: {formatTimestamp(task.started_at)}
                      </Typography>
                      
                      {task.status === 'running' && (
                        <Box sx={{ mb: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={task.progress}
                            sx={{ mb: 1 }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            Progress: {task.progress}%
                          </Typography>
                        </Box>
                      )}
                      
                      {task.error && (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          {task.error}
                        </Alert>
                      )}
                      
                      {task.result && task.status === 'completed' && (
                        <Paper sx={{ p: 2, mt: 1, backgroundColor: 'success.light' }}>
                          <Typography variant="subtitle2" color="success.contrastText">
                            Task completed successfully
                          </Typography>
                          <Typography variant="body2" color="success.contrastText">
                            {JSON.stringify(task.result, null, 2)}
                          </Typography>
                        </Paper>
                      )}
                    </Box>
                  }
                />
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {task.status === 'running' && (
                    <Tooltip title="Cancel Task">
                      <IconButton
                        color="error"
                        onClick={() => handleCancelTask(task.task_id)}
                      >
                        <Stop />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              </ListItem>
              {index < tasks.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Schedule sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
            No background tasks
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Background tasks will appear here when they are created
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default BackgroundTasks;
