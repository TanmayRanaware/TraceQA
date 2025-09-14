import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Alert,
  LinearProgress,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import {
  Upload,
  Description,
  CheckCircle,
  Error,
  CloudUpload,
  FileUpload,
  Schedule,
  Add,
  Business,
} from '@mui/icons-material';
import axios from 'axios';

interface Journey {
  name: string;
  description: string;
  color: string;
}

interface SourceType {
  value: string;
  label: string;
  description: string;
  icon: string;
}

const DocumentUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedJourney, setSelectedJourney] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [notes, setNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Journey management
  const [journeys, setJourneys] = useState<Journey[]>([]);
  const [sourceTypes, setSourceTypes] = useState<SourceType[]>([]);
  const [journeyMode, setJourneyMode] = useState<'existing' | 'new'>('existing');
  const [newJourneyName, setNewJourneyName] = useState('');
  const [newJourneyDescription, setNewJourneyDescription] = useState('');
  const [showNewJourneyDialog, setShowNewJourneyDialog] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch journeys and source types on component mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        // Fetch journeys from the new journey management API
        const journeysResponse = await axios.get('/api/journeys/');
        setJourneys(journeysResponse.data.journeys);
        // Fetch source types from config
        const configResponse = await axios.get('/api/config/');
        setSourceTypes(configResponse.data.source_types);
      } catch (err) {
        console.error('Failed to fetch configuration:', err);
        setError('Failed to load configuration');
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleJourneyModeChange = (
    event: React.MouseEvent<HTMLElement>,
    newMode: 'existing' | 'new' | null,
  ) => {
    if (newMode !== null) {
      setJourneyMode(newMode);
      setSelectedJourney('');
    }
  };

  const handleCreateNewJourney = async () => {
    if (newJourneyName.trim()) {
      try {
        const response = await axios.post('/api/journeys/create', {
          name: newJourneyName.trim(),
          description: newJourneyDescription.trim() || 'Custom journey',
          color: 'primary'
        });
        
        if (response.data.status === 'success') {
          // Add the new journey to the local state
          setJourneys(prev => [...prev, response.data.journey]);
          setSelectedJourney(newJourneyName.trim());
          setNewJourneyName('');
          setNewJourneyDescription('');
          setShowNewJourneyDialog(false);
          setJourneyMode('existing');
        } else {
          setError(response.data.message || 'Failed to create journey');
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to create journey');
        console.error('Journey creation error:', err);
      }
    }
  };

  const handleUpload = async () => {
    // Determine the journey name based on mode
    const journeyName = journeyMode === 'existing' ? selectedJourney : newJourneyName.trim();
    
    if (!selectedFile || !journeyName || !sourceType) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setUploading(true);
      setError(null);

      // If creating a new journey, create it first
      if (journeyMode === 'new') {
        const journeyResponse = await axios.post('/api/journeys/create', {
          name: newJourneyName.trim(),
          description: newJourneyDescription.trim() || 'Custom journey',
          color: 'primary'
        });
        
        if (journeyResponse.data.status === 'success') {
          // Add the new journey to the local state
          setJourneys(prev => [...prev, journeyResponse.data.journey]);
        } else {
          setError(journeyResponse.data.message || 'Failed to create journey');
          setUploading(false);
          return;
        }
      }

      // First upload the file
      const formData = new FormData();
      formData.append('file', selectedFile);

      const uploadResponse = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Then ingest the requirement
      const ingestResponse = await axios.post('/requirements/ingest', {
        journey: journeyName,
        document_uri: uploadResponse.data.uri,
        source_type: sourceType,
        effective_date: effectiveDate || undefined,
        notes: notes || undefined,
      });

      setUploadResult(ingestResponse.data);
      
      // Reset form
      setSelectedFile(null);
      setSelectedJourney(journeyMode === 'new' ? newJourneyName.trim() : '');
      setSourceType('');
      setEffectiveDate('');
      setNotes('');
      setNewJourneyName('');
      setNewJourneyDescription('');
      setJourneyMode('existing');
      
      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf': return <Description color="error" />;
      case 'docx': return <Description color="primary" />;
      case 'txt': return <Description color="success" />;
      default: return <Description color="inherit" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <Box>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" sx={{ mb: 1, fontWeight: 700 }}>
            Document Upload
          </Typography>
          <Typography variant="h6" sx={{ color: 'text.secondary' }}>
            Upload and ingest requirement documents for AI-powered analysis
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <LinearProgress sx={{ width: '50%' }} />
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" sx={{ mb: 1, fontWeight: 700 }}>
          Document Upload
        </Typography>
        <Typography variant="h6" sx={{ color: 'text.secondary' }}>
          Upload and ingest requirement documents for AI-powered analysis
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        {/* Upload Form */}
        <Box sx={{ flex: 1 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <FileUpload />
                Upload Document
              </Typography>

              {/* File Selection */}
              <Box sx={{ mb: 3 }}>
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <Button
                  variant="outlined"
                  component="label"
                  htmlFor="file-input"
                  startIcon={<CloudUpload />}
                  fullWidth
                  sx={{ py: 3, borderStyle: 'dashed' }}
                >
                  {selectedFile ? selectedFile.name : 'Choose File'}
                </Button>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Supported formats: PDF, DOCX, TXT (Max 50MB)
                </Typography>
              </Box>

              {/* Journey Selection */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                  Journey Selection *
                </Typography>
                
                <ToggleButtonGroup
                  value={journeyMode}
                  exclusive
                  onChange={handleJourneyModeChange}
                  aria-label="journey mode"
                  sx={{ mb: 2 }}
                >
                  <ToggleButton value="existing" aria-label="existing journey">
                    <Business sx={{ mr: 1 }} />
                    Choose Existing
                  </ToggleButton>
                  <ToggleButton value="new" aria-label="new journey">
                    <Add sx={{ mr: 1 }} />
                    Create New
                  </ToggleButton>
                </ToggleButtonGroup>

                {journeyMode === 'existing' ? (
                  <FormControl fullWidth>
                    <InputLabel>Select Journey</InputLabel>
                    <Select
                      value={selectedJourney}
                      label="Select Journey"
                      onChange={(e: SelectChangeEvent) => setSelectedJourney(e.target.value)}
                    >
                      {journeys.map((journey) => (
                        <MenuItem key={journey.name} value={journey.name}>
                          <Box>
                            <Typography variant="body1">{journey.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {journey.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                ) : (
                  <Box>
                    <TextField
                      fullWidth
                      label="Journey Name"
                      value={newJourneyName}
                      onChange={(e) => setNewJourneyName(e.target.value)}
                      placeholder="e.g., Risk Management, Compliance"
                      sx={{ mb: 2 }}
                    />
                    <TextField
                      fullWidth
                      label="Description (Optional)"
                      value={newJourneyDescription}
                      onChange={(e) => setNewJourneyDescription(e.target.value)}
                      placeholder="Brief description of this journey"
                      multiline
                      rows={2}
                    />
                  </Box>
                )}
              </Box>

              {/* Source Type Selection */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                  Source Type *
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Source Type *</InputLabel>
                  <Select
                    value={sourceType}
                    label="Source Type *"
                    onChange={(e: SelectChangeEvent) => setSourceType(e.target.value)}
                    sx={{ zIndex: 1 }}
                  >
                    {sourceTypes.map((type) => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {sourceTypes.length === 0 && (
                  <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                    No source types available. Please refresh the page.
                  </Typography>
                )}
              </Box>

              <TextField
                fullWidth
                label="Effective Date"
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                sx={{ mb: 2 }}
                InputLabelProps={{ shrink: true }}
              />

              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional notes about this document..."
                sx={{ mb: 3 }}
              />

              <Button
                fullWidth
                variant="contained"
                onClick={handleUpload}
                disabled={
                  !selectedFile || 
                  !sourceType || 
                  uploading || 
                  loading ||
                  (journeyMode === 'existing' && !selectedJourney) ||
                  (journeyMode === 'new' && !newJourneyName.trim())
                }
                startIcon={<Upload />}
                size="large"
              >
                {uploading ? 'Uploading...' : 'Upload & Ingest'}
              </Button>

              {uploading && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                    Processing document with AI...
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Results & Status */}
        <Box sx={{ flex: 1 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircle />
                Upload Status
              </Typography>

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              {uploadResult && (
                <Paper sx={{ p: 3, backgroundColor: 'success.light' }}>
                  <Typography variant="h6" color="success.contrastText" sx={{ mb: 2 }}>
                    Document Successfully Ingested!
                  </Typography>
                  
                  <List dense>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Journey"
                        secondary={uploadResult.journey}
                      />
                    </ListItem>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Version ID"
                        secondary={uploadResult.version}
                      />
                    </ListItem>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Chunks Indexed"
                        secondary={uploadResult.chunks_indexed}
                      />
                    </ListItem>
                  </List>

                  <Box sx={{ mt: 2 }}>
                    <Chip
                      label="Ready for Search"
                      color="success"
                      icon={<CheckCircle />}
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label="AI Analysis Complete"
                      color="success"
                      icon={<CheckCircle />}
                    />
                  </Box>
                </Paper>
              )}

              {/* File Info */}
              {selectedFile && (
                <Paper sx={{ p: 2, mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Selected File:
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getFileIcon(selectedFile.name)}
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {selectedFile.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatFileSize(selectedFile.size)}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              )}

              {/* Upload Guidelines */}
              <Paper sx={{ p: 2, mt: 2, backgroundColor: 'info.light' }}>
                <Typography variant="subtitle2" color="info.contrastText" sx={{ mb: 1 }}>
                  Upload Guidelines:
                </Typography>
                <Typography variant="body2" color="info.contrastText" sx={{ mb: 1 }}>
                  • Choose an existing journey or create a new one for your document
                </Typography>
                <Typography variant="body2" color="info.contrastText" sx={{ mb: 1 }}>
                  • Ensure documents are clear and readable
                </Typography>
                <Typography variant="body2" color="info.contrastText" sx={{ mb: 1 }}>
                  • PDFs should have selectable text (not scanned images)
                </Typography>
                <Typography variant="body2" color="info.contrastText" sx={{ mb: 1 }}>
                  • Documents will be automatically chunked and indexed
                </Typography>
                <Typography variant="body2" color="info.contrastText">
                  • AI will generate summaries and extract key information
                </Typography>
              </Paper>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* New Journey Dialog */}
      <Dialog 
        open={showNewJourneyDialog} 
        onClose={() => setShowNewJourneyDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Journey</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Journey Name"
            fullWidth
            variant="outlined"
            value={newJourneyName}
            onChange={(e) => setNewJourneyName(e.target.value)}
            placeholder="e.g., Risk Management, Compliance"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description (Optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newJourneyDescription}
            onChange={(e) => setNewJourneyDescription(e.target.value)}
            placeholder="Brief description of this journey"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowNewJourneyDialog(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreateNewJourney}
            variant="contained"
            disabled={!newJourneyName.trim()}
          >
            Create Journey
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentUpload;
