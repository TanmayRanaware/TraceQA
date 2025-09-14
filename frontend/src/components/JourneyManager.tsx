import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Business,
} from '@mui/icons-material';
import axios from 'axios';

interface Journey {
  name: string;
  description: string;
  color: string;
  created_date: string;
  is_default: boolean;
}

const JourneyManager: React.FC = () => {
  const [journeys, setJourneys] = useState<Journey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingJourney, setEditingJourney] = useState<Journey | null>(null);
  const [newJourney, setNewJourney] = useState({
    name: '',
    description: '',
    color: 'primary'
  });

  // Fetch journeys
  const fetchJourneys = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/journeys/');
      setJourneys(response.data.journeys);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch journeys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJourneys();
  }, []);

  const handleCreateJourney = async () => {
    if (!newJourney.name.trim()) return;

    try {
      const response = await axios.post('/api/journeys/create', newJourney);
      if (response.data.status === 'success') {
        setJourneys(prev => [...prev, response.data.journey]);
        setNewJourney({ name: '', description: '', color: 'primary' });
        setShowCreateDialog(false);
        setError(null);
      } else {
        setError(response.data.message || 'Failed to create journey');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create journey');
    }
  };

  const handleUpdateJourney = async () => {
    if (!editingJourney) return;

    try {
      const response = await axios.put('/api/journeys/update', {
        old_name: editingJourney.name,
        new_name: editingJourney.name,
        description: editingJourney.description,
        color: editingJourney.color
      });
      
      if (response.data.status === 'success') {
        setJourneys(prev => prev.map(j => 
          j.name === editingJourney.name ? response.data.journey : j
        ));
        setShowEditDialog(false);
        setEditingJourney(null);
        setError(null);
      } else {
        setError(response.data.message || 'Failed to update journey');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update journey');
    }
  };

  const handleDeleteJourney = async (journey: Journey) => {
    if (journey.is_default) {
      setError('Cannot delete default journeys');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete "${journey.name}"?`)) {
      return;
    }

    try {
      const response = await axios.delete('/api/journeys/delete', {
        data: { name: journey.name }
      });
      
      if (response.data.status === 'success') {
        setJourneys(prev => prev.filter(j => j.name !== journey.name));
        setError(null);
      } else {
        setError(response.data.message || 'Failed to delete journey');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete journey');
    }
  };

  const openEditDialog = (journey: Journey) => {
    setEditingJourney({ ...journey });
    setShowEditDialog(true);
  };

  const getColorChip = (color: string) => {
    const colorMap: { [key: string]: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'default' } = {
      'primary': 'primary',
      'secondary': 'secondary',
      'success': 'success',
      'warning': 'warning',
      'error': 'error',
      'info': 'info',
    };
    return colorMap[color] || 'default';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Business />
          Journey Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setShowCreateDialog(true)}
        >
          Add Journey
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <List>
            {journeys.map((journey) => (
              <ListItem key={journey.name} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="h6">{journey.name}</Typography>
                      <Chip 
                        label={journey.color} 
                        color={getColorChip(journey.color)} 
                        size="small" 
                      />
                      {journey.is_default && (
                        <Chip label="Default" color="default" size="small" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {journey.description}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Created: {new Date(journey.created_date).toLocaleDateString()}
                      </Typography>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={() => openEditDialog(journey)}
                    disabled={journey.is_default}
                  >
                    <Edit />
                  </IconButton>
                  <IconButton
                    edge="end"
                    onClick={() => handleDeleteJourney(journey)}
                    disabled={journey.is_default}
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      {/* Create Journey Dialog */}
      <Dialog open={showCreateDialog} onClose={() => setShowCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Journey</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Journey Name"
            fullWidth
            variant="outlined"
            value={newJourney.name}
            onChange={(e) => setNewJourney(prev => ({ ...prev, name: e.target.value }))}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newJourney.description}
            onChange={(e) => setNewJourney(prev => ({ ...prev, description: e.target.value }))}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Color"
            fullWidth
            variant="outlined"
            value={newJourney.color}
            onChange={(e) => setNewJourney(prev => ({ ...prev, color: e.target.value }))}
            helperText="primary, secondary, success, warning, error, info"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateJourney}
            variant="contained"
            disabled={!newJourney.name.trim()}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Journey Dialog */}
      <Dialog open={showEditDialog} onClose={() => setShowEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Journey</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Journey Name"
            fullWidth
            variant="outlined"
            value={editingJourney?.name || ''}
            onChange={(e) => setEditingJourney(prev => prev ? { ...prev, name: e.target.value } : null)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={editingJourney?.description || ''}
            onChange={(e) => setEditingJourney(prev => prev ? { ...prev, description: e.target.value } : null)}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Color"
            fullWidth
            variant="outlined"
            value={editingJourney?.color || ''}
            onChange={(e) => setEditingJourney(prev => prev ? { ...prev, color: e.target.value } : null)}
            helperText="primary, secondary, success, warning, error, info"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleUpdateJourney}
            variant="contained"
            disabled={!editingJourney?.name.trim()}
          >
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default JourneyManager;
