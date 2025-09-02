import React, { useState } from 'react';
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
} from '@mui/material';
import {
  Upload,
  Description,
  CheckCircle,
  Error,
  CloudUpload,
  FileUpload,
  Schedule,
} from '@mui/icons-material';
import axios from 'axios';

const DocumentUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedJourney, setSelectedJourney] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [notes, setNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const journeys = ['Point of Settlement', 'Payment Processing', 'Account Management'];
  const sourceTypes = [
    { value: 'fsd', label: 'FSD (Functional Specification Document)' },
    { value: 'addendum', label: 'Addendum' },
    { value: 'annexure', label: 'Annexure' },
    { value: 'email', label: 'Email Communication' },
  ];

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !selectedJourney || !sourceType) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setUploading(true);
      setError(null);

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
        journey: selectedJourney,
        document_uri: uploadResponse.data.uri,
        source_type: sourceType,
        effective_date: effectiveDate || undefined,
        notes: notes || undefined,
      });

      setUploadResult(ingestResponse.data);
      
      // Reset form
      setSelectedFile(null);
      setSelectedJourney('');
      setSourceType('');
      setEffectiveDate('');
      setNotes('');
      
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

              {/* Form Fields */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Journey *</InputLabel>
                <Select
                  value={selectedJourney}
                  label="Journey *"
                  onChange={(e: SelectChangeEvent) => setSelectedJourney(e.target.value)}
                >
                  {journeys.map((journey) => (
                    <MenuItem key={journey} value={journey}>
                      {journey}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Source Type *</InputLabel>
                <Select
                  value={sourceType}
                  label="Source Type *"
                  onChange={(e: SelectChangeEvent) => setSourceType(e.target.value)}
                >
                  {sourceTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

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
                disabled={!selectedFile || !selectedJourney || !sourceType || uploading}
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
    </Box>
  );
};

export default DocumentUpload;
