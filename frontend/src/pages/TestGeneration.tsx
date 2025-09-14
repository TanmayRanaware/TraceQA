import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  Paper,
  Alert,
  LinearProgress,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  BugReport,
  PlayArrow,
  Schedule,
  Settings,
  Download,
  TableView,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRenderCellParams, GridValueGetterParams } from '@mui/x-data-grid';
import axios from 'axios';

const TestGeneration: React.FC = () => {
  const [selectedJourney, setSelectedJourney] = useState('');
  const [maxCases, setMaxCases] = useState(100);
  const [contextTopK, setContextTopK] = useState(20);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [generatedTests, setGeneratedTests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryable, setRetryable] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const journeys = ['Point of Settlement', 'Payment Processing', 'Account Management'];
  const providers = ['claude', 'gemini', 'ollama', 'openai'];
  const models = {
    claude: ['claude-3-5-haiku-20241022', 'claude-3-haiku-20240307'],
    gemini: ['gemini-2.0-flash', 'gemini-1.5-pro'],
    ollama: ['llama3.1:8b-instruct', 'llama3.1:70b-instruct', 'mistral:7b-instruct'],
    openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
  };

  const handleGenerateTests = async () => {
    if (!selectedJourney) return;

    try {
      setLoading(true);
      setError(null);
      setRetryable(false);
      
      const response = await axios.post('/api/tests/generate', {
        journey: selectedJourney,
        max_cases: maxCases,
        context_top_k: contextTopK,
        provider: selectedProvider || undefined,
        model: selectedModel || undefined,
      });
      
      // Check if the response indicates an error with retry suggestion
      if (response.data.debug?.status === 'error' && response.data.debug?.retry_suggested) {
        setError(response.data.debug.message);
        setRetryable(true);
      } else {
        setGeneratedTests(response.data.tests);
      }
    } catch (err: any) {
      let errorMessage = err.response?.data?.detail || 'Failed to generate tests';
      let isRetryable = false;
      
      // Check for retryable error conditions
      if (errorMessage.includes('temporarily unavailable') || 
          errorMessage.includes('high demand') ||
          errorMessage.includes('503') ||
          errorMessage.includes('timeout') ||
          errorMessage.includes('rate limit')) {
        isRetryable = true;
      }
      
      setError(errorMessage);
      setRetryable(isRetryable);
      console.error('Test generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchGeneration = async () => {
    if (!selectedJourney) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/background/batch-test-generation', null, {
        params: {
          journey: selectedJourney,
          max_cases: maxCases,
          context_top_k: contextTopK,
          provider: selectedProvider || undefined,
        },
      });
      
      // Show success message with task ID
      setError(null);
      alert(`Batch generation started! Task ID: ${response.data.task_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start batch generation');
      console.error('Batch generation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    if (generatedTests.length === 0) return;

    try {
      const response = await axios.post('/api/tests/export-excel', generatedTests, {
        responseType: 'blob',
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'test_cases.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export test cases to Excel');
      console.error('Export error:', err);
    }
  };

  const getTestTypeColor = (title: string) => {
    if (title.toLowerCase().includes('happy') || title.toLowerCase().includes('positive')) {
      return 'success';
    } else if (title.toLowerCase().includes('negative') || title.toLowerCase().includes('error')) {
      return 'error';
    } else if (title.toLowerCase().includes('boundary')) {
      return 'warning';
    } else {
      return 'default';
    }
  };

  // Define DataGrid columns
  const columns: GridColDef[] = [
    { 
      field: 'key', 
      headerName: 'Key', 
      width: 100
    },
    { 
      field: 'name', 
      headerName: 'Name', 
      width: 250
    },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 100,
      renderCell: (params: GridRenderCellParams) => (
        <Chip 
          label={params.row.status || 'Draft'} 
          color="default" 
          size="small" 
        />
      )
    },
    { 
      field: 'precondition_objective', 
      headerName: 'Precondition Objective', 
      width: 200
    },
    { 
      field: 'folder', 
      headerName: 'Folder', 
      width: 150
    },
    { 
      field: 'priority', 
      headerName: 'Priority', 
      width: 100,
      renderCell: (params: GridRenderCellParams) => {
        const priority = params.row.priority || 'Medium';
        const color = priority === 'High' ? 'error' : priority === 'Low' ? 'success' : 'warning';
        return <Chip label={priority} color={color} size="small" />;
      }
    },
    { 
      field: 'component_labels_str', 
      headerName: 'Component Labels', 
      width: 180
    },
    { 
      field: 'owner', 
      headerName: 'Owner', 
      width: 120
    },
    { 
      field: 'estimated_time', 
      headerName: 'Estimated Time', 
      width: 130
    },
    { 
      field: 'coverage', 
      headerName: 'Coverage', 
      width: 150
    },
    { 
      field: 'test_script', 
      headerName: 'Test Script', 
      width: 300
    }
  ];

  // Prepare data for DataGrid
  const gridData = generatedTests.map((test: any, index: number) => ({
    id: index + 1,
    key: test.key || test.test_id || `TC${String(index + 1).padStart(3, '0')}`,
    name: test.name || test.title || 'Untitled Test',
    status: test.status || 'Draft',
    precondition_objective: test.precondition_objective || 'N/A',
    folder: test.folder || selectedJourney,
    priority: test.priority || 'Medium',
    component_labels_str: Array.isArray(test.component_labels) 
      ? test.component_labels.join(', ') 
      : test.component_labels || 'N/A',
    owner: test.owner || 'QA Team',
    estimated_time: test.estimated_time || 'N/A',
    coverage: test.coverage || 'N/A',
    test_script: test.test_script || 'N/A'
  }));

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" sx={{ mb: 1, fontWeight: 700 }}>
          Test Case Generation
        </Typography>
        <Typography variant="h6" sx={{ color: 'text.secondary' }}>
          Generate comprehensive test cases using AI-powered analysis of requirements
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        {/* Configuration Panel */}
        <Box sx={{ flex: '1 1 400px', minWidth: '350px' }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Settings />
                Configuration
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Journey</InputLabel>
                <Select
                  value={selectedJourney}
                  label="Journey"
                  onChange={(e: SelectChangeEvent) => setSelectedJourney(e.target.value)}
                >
                  {journeys.map((journey) => (
                    <MenuItem key={journey} value={journey}>
                      {journey}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Maximum Test Cases"
                type="number"
                value={maxCases}
                onChange={(e) => setMaxCases(parseInt(e.target.value) || 100)}
                sx={{ mb: 2 }}
                inputProps={{ min: 1, max: 1000 }}
              />

              <TextField
                fullWidth
                label="Context Retrieval (Top-K)"
                type="number"
                value={contextTopK}
                onChange={(e) => setContextTopK(parseInt(e.target.value) || 20)}
                sx={{ mb: 2 }}
                inputProps={{ min: 5, max: 100 }}
                helperText="Number of requirement chunks to consider"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={showAdvanced}
                    onChange={(e) => setShowAdvanced(e.target.checked)}
                  />
                }
                label="Advanced Options"
                sx={{ mb: 2 }}
              />

              {showAdvanced && (
                <>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Provider</InputLabel>
                    <Select
                      value={selectedProvider}
                      label="Provider"
                      onChange={(e: SelectChangeEvent) => setSelectedProvider(e.target.value)}
                    >
                      <MenuItem value="">Auto-detect</MenuItem>
                      {providers.map((provider) => (
                        <MenuItem key={provider} value={provider}>
                          {provider.charAt(0).toUpperCase() + provider.slice(1)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Model</InputLabel>
                    <Select
                      value={selectedModel}
                      label="Model"
                      onChange={(e: SelectChangeEvent) => setSelectedModel(e.target.value)}
                      disabled={!selectedProvider}
                    >
                      <MenuItem value="">Auto-select</MenuItem>
                      {selectedProvider && models[selectedProvider as keyof typeof models]?.map((model) => (
                        <MenuItem key={model} value={model}>
                          {model}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </>
              )}

              <Box sx={{ mt: 3 }}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleGenerateTests}
                  disabled={!selectedJourney || loading}
                  startIcon={<BugReport />}
                  sx={{ mb: 2 }}
                >
                  Generate Tests
                </Button>
                
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={handleBatchGeneration}
                  disabled={!selectedJourney || loading}
                  startIcon={<Schedule />}
                >
                  Start Batch Generation
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Results Panel */}
        <Box sx={{ flex: '2 1 600px', minWidth: '500px' }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TableView />
                  Generated Test Cases
                  {generatedTests.length > 0 && (
                    <Chip label={generatedTests.length} color="primary" size="small" />
                  )}
                </Typography>
                {generatedTests.length > 0 && (
                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={handleExportExcel}
                    size="small"
                  >
                    Export to Excel
                  </Button>
                )}
              </Box>

              {loading && (
                <Box sx={{ mb: 3 }}>
                  <LinearProgress />
                  <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                    Generating test cases using AI...
                  </Typography>
                </Box>
              )}

              {error && (
                <Alert 
                  severity="error" 
                  sx={{ mb: 3 }}
                  action={
                    retryable ? (
                      <Button 
                        color="inherit" 
                        size="small" 
                        onClick={handleGenerateTests}
                        disabled={loading}
                      >
                        Retry
                      </Button>
                    ) : null
                  }
                >
                  {error}
                  {retryable && (
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      💡 This appears to be a temporary issue. Please try again.
                    </Typography>
                  )}
                </Alert>
              )}

              {generatedTests.length > 0 ? (
                <Box sx={{ height: 600, width: '100%' }}>
                  <DataGrid
                    rows={gridData}
                    columns={columns}
                    initialState={{
                      pagination: {
                        paginationModel: {
                          pageSize: 10,
                        },
                      },
                    }}
                    pageSizeOptions={[10, 25, 50]}
                    checkboxSelection
                    disableRowSelectionOnClick
                    sx={{
                      '& .MuiDataGrid-cell': {
                        fontSize: '0.875rem',
                      },
                      '& .MuiDataGrid-columnHeaders': {
                        backgroundColor: 'rgba(0, 0, 0, 0.02)',
                        fontWeight: 600,
                      },
                    }}
                  />
                </Box>
              ) : (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <BugReport sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                    No test cases generated yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Configure the parameters and click "Generate Tests" to create test cases
                  </Typography>
                </Paper>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default TestGeneration;
