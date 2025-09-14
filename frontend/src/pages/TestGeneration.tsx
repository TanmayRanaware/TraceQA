import React, { useState, useEffect } from 'react';
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
  Refresh,
  Email,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRenderCellParams, GridValueGetterParams } from '@mui/x-data-grid';
import axios from 'axios';

const TestGeneration: React.FC = () => {
  const [selectedJourney, setSelectedJourney] = useState('');
  const [maxCases, setMaxCases] = useState(100);
  const [contextTopK, setContextTopK] = useState(20);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [generatedTests, setGeneratedTests] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryable, setRetryable] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showChangeManagement, setShowChangeManagement] = useState(false);
  
  // Email state
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailSuccess, setEmailSuccess] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [totalPages, setTotalPages] = useState(1);
  const [totalAvailable, setTotalAvailable] = useState(0);
  const [allTests, setAllTests] = useState<any[]>([]); // Store all generated tests

  const [journeys, setJourneys] = useState<string[]>([]);
  const providers = ['claude', 'gemini', 'ollama', 'openai'];

  // Fetch journeys on component mount - only those with uploaded documents
  useEffect(() => {
    const fetchJourneys = async () => {
      try {
        // Fetch only journeys that have uploaded documents
        const response = await axios.get('/requirements/versions');
        const journeysWithDocs = response.data.versions.map((v: any) => v.journey);
        setJourneys(journeysWithDocs);
      } catch (err) {
        console.error('Failed to fetch journeys:', err);
        // Fallback to empty array if no documents uploaded
        setJourneys([]);
      }
    };

    fetchJourneys();
  }, []);

  // Refresh journeys function
  const refreshJourneys = async () => {
    try {
      // Fetch only journeys that have uploaded documents
      const response = await axios.get('/requirements/versions');
      const journeysWithDocs = response.data.versions.map((v: any) => v.journey);
      setJourneys(journeysWithDocs);
    } catch (err) {
      console.error('Failed to refresh journeys:', err);
      setJourneys([]);
    }
  };

  const models = {
    claude: ['claude-3-5-haiku-20241022', 'claude-3-haiku-20240307'],
    gemini: ['gemini-2.0-flash', 'gemini-1.5-pro'],
    ollama: ['llama3.1:8b-instruct', 'llama3.1:70b-instruct', 'mistral:7b-instruct'],
    openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
  };

  const handleGenerateTests = async (page: number = 1, append: boolean = false) => {
    if (!selectedJourney) return;

    try {
      setLoading(true);
      setError(null);
      setRetryable(false);
      
      const response = await axios.post('/api/tests/generate', {
        journey: selectedJourney,
        max_cases: maxCases,
        context_top_k: contextTopK,
        page: page,
        provider: selectedProvider || undefined,
        model: selectedModel || undefined,
      });
      
      // Check if the response indicates an error with retry suggestion
      if (response.data.debug?.status === 'error' && response.data.debug?.retry_suggested) {
        setError(response.data.debug.message);
        setRetryable(true);
      } else {
        const newTests = response.data.tests || [];
        
        if (append && page > 1) {
          // Append to existing tests for pagination
          setAllTests(prev => [...prev, ...newTests]);
          setGeneratedTests(prev => [...prev, ...newTests]);
        } else {
          // Replace tests for new generation
          setAllTests(newTests);
          setGeneratedTests(newTests);
        }
        
        // Update pagination state
        setCurrentPage(response.data.pagination?.page || 1);
        setHasNextPage(response.data.pagination?.has_next_page || false);
        setTotalPages(response.data.pagination?.total_pages || 1);
        setTotalAvailable(response.data.pagination?.total_available || 0);
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

  const handleNextPage = () => {
    if (hasNextPage) {
      handleGenerateTests(currentPage + 1, true);
    }
  };

  const handleReset = () => {
    setCurrentPage(1);
    setHasNextPage(false);
    setTotalPages(1);
    setTotalAvailable(0);
    setAllTests([]);
    setGeneratedTests([]);
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
      link.setAttribute('download', 'test_cases_structured.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export test cases to Excel');
      console.error('Export error:', err);
    }
  };

  const handleSendToBA = async () => {
    if (generatedTests.length === 0 || !selectedJourney) return;

    try {
      setSendingEmail(true);
      setEmailError(null);
      setEmailSuccess(null);

      const response = await axios.post('/api/tests/send-to-ba', {
        tests: generatedTests,
        journey: selectedJourney
      });

      if (response.data.success) {
        setEmailSuccess(response.data.message);
        // Clear success message after 5 seconds
        setTimeout(() => setEmailSuccess(null), 5000);
      } else {
        setEmailError(response.data.message || 'Failed to send email');
      }
    } catch (err: any) {
      setEmailError(err.response?.data?.detail || 'Failed to send email to BA');
      console.error('Email error:', err);
    } finally {
      setSendingEmail(false);
    }
  };

  const handleValidateTestCases = async () => {
    if (!selectedJourney) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/tests/validate-test-cases', {
        journey: selectedJourney,
        validate_outdated: true,
        remove_outdated: true
      });
      
      if (response.data.status === 'success') {
        alert(`Validation completed! Found ${response.data.outdated_cases_found} outdated cases, removed ${response.data.outdated_cases_removed} cases.`);
      } else {
        setError(response.data.message || 'Validation failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate test cases');
      console.error('Validation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChangeManagement = async (action: string, documentUri: string, sourceType: string) => {
    if (!selectedJourney) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/tests/change-management', {
        journey: selectedJourney,
        document_uri: documentUri,
        source_type: sourceType,
        action: action
      });
      
      if (response.data.status === 'success') {
        alert(`Change management completed! ${response.data.message}`);
        // Refresh test cases if new ones were generated
        if (response.data.new_test_cases) {
          setGeneratedTests(prev => [...prev, ...response.data.new_test_cases]);
        }
      } else {
        setError(response.data.message || 'Change management failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to handle requirement change');
      console.error('Change management error:', err);
    } finally {
      setLoading(false);
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

  // Define DataGrid columns for Objective A structured format
  const columns: GridColDef[] = [
    { 
      field: 'test_case_name', 
      headerName: 'Test Case Name', 
      width: 250,
      renderCell: (params: GridRenderCellParams) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {params.row.test_case_name || params.row.name || params.row.title || 'Untitled Test'}
        </Typography>
      )
    },
    { 
      field: 'preconditions', 
      headerName: 'Preconditions', 
      width: 200
    },
    { 
      field: 'steps', 
      headerName: 'Steps', 
      width: 300
    },
    { 
      field: 'expected_result', 
      headerName: 'Expected Result', 
      width: 200
    },
    { 
      field: 'actual_result', 
      headerName: 'Actual Result', 
      width: 200
    },
    { 
      field: 'test_type', 
      headerName: 'Test Type', 
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const testType = params.row.test_type || 'positive';
        const color = testType === 'positive' ? 'success' : 
                     testType === 'negative' ? 'error' : 'warning';
        const label = testType === 'positive' ? 'Positive' :
                     testType === 'negative' ? 'Negative' : 'Edge';
        return <Chip label={label} color={color} size="small" />;
      }
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
      field: 'journey', 
      headerName: 'Journey', 
      width: 150
    },
    { 
      field: 'requirement_reference', 
      headerName: 'Requirement Reference', 
      width: 180
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
      field: 'test_case_id', 
      headerName: 'Test Case ID', 
      width: 120
    }
  ];

  // Prepare data for DataGrid with structured format
  const gridData = generatedTests.map((test: any, index: number) => ({
    id: index + 1,
    // New structured format fields
    test_case_name: test.test_case_name || test.name || test.title || 'Untitled Test',
    preconditions: test.preconditions || test.precondition_objective || 'N/A',
    steps: test.steps || test.test_script || 'N/A',
    expected_result: test.expected_result || test.expected || 'N/A',
    actual_result: test.actual_result || '',
    test_type: test.test_type || 'positive',
    priority: test.priority || 'Medium',
    journey: test.journey || selectedJourney,
    requirement_reference: test.requirement_reference || 'N/A',
    status: test.status || 'Draft',
    test_case_id: test.test_case_id || test.key || test.test_id || `TC${String(index + 1).padStart(3, '0')}`,
    // Legacy fields for backward compatibility
    key: test.key || test.test_id || `TC${String(index + 1).padStart(3, '0')}`,
    name: test.name || test.title || 'Untitled Test',
    status_legacy: test.status || 'Draft',
    precondition_objective: test.precondition_objective || 'N/A',
    folder: test.folder || selectedJourney,
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

              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <FormControl fullWidth>
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
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={refreshJourneys}
                  sx={{ minWidth: 'auto', px: 2 }}
                  title="Refresh journeys with uploaded documents"
                >
                  Refresh
                </Button>
              </Box>

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

              <FormControlLabel
                control={
                  <Switch
                    checked={showChangeManagement}
                    onChange={(e) => setShowChangeManagement(e.target.checked)}
                  />
                }
                label="Change Management"
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

              {showChangeManagement && (
                <Box sx={{ mt: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                  <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                    Change Management
                  </Typography>
                  
                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={handleValidateTestCases}
                    disabled={!selectedJourney || loading}
                    sx={{ mb: 1 }}
                  >
                    Validate & Remove Outdated Cases
                  </Button>
                  
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                    Scans existing test cases and removes those that no longer match current requirements
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleChangeManagement('add', 'new-document.pdf', 'fsd')}
                      disabled={!selectedJourney || loading}
                    >
                      Add New Requirement
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleChangeManagement('update', 'updated-document.pdf', 'addendum')}
                      disabled={!selectedJourney || loading}
                    >
                      Update Requirement
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleChangeManagement('remove', 'old-document.pdf', 'annexure')}
                      disabled={!selectedJourney || loading}
                    >
                      Remove Requirement
                    </Button>
                  </Box>
                </Box>
              )}

              <Box sx={{ mt: 3 }}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={() => handleGenerateTests(1, false)}
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
                  sx={{ mb: 2 }}
                >
                  Start Batch Generation
                </Button>

                {/* Pagination Controls */}
                {generatedTests.length > 0 && (
                  <Box sx={{ mt: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Pagination
                    </Typography>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Page {currentPage} of {totalPages} • {allTests.length} total test cases
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {totalAvailable} documents available
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                      <Button
                        variant="outlined"
                        onClick={handleReset}
                        disabled={loading}
                        size="small"
                      >
                        Reset
                      </Button>
                      <Button
                        variant="contained"
                        onClick={handleNextPage}
                        disabled={!hasNextPage || loading}
                        size="small"
                      >
                        Load More Tests &gt;
                      </Button>
                    </Box>
                    
                    {hasNextPage && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 1 }}>
                        Click "Load More Tests" to generate test cases from next {contextTopK} document chunks
                      </Typography>
                    )}
                  </Box>
                )}
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
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      startIcon={<Download />}
                      onClick={handleExportExcel}
                      size="small"
                    >
                      Export to Excel
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<Email />}
                      onClick={handleSendToBA}
                      disabled={sendingEmail || !selectedJourney}
                      size="small"
                      color="primary"
                    >
                      {sendingEmail ? 'Sending...' : 'Send to BA'}
                    </Button>
                  </Box>
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
                        onClick={() => handleGenerateTests(1, false)}
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

              {emailSuccess && (
                <Alert severity="success" sx={{ mb: 3 }}>
                  {emailSuccess}
                </Alert>
              )}

              {emailError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {emailError}
                </Alert>
              )}

              {generatedTests.length > 0 ? (
                <Box>
                  {/* Test Case Summary */}
                  <Box sx={{ mb: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="h6" sx={{ mb: 2 }}>
                      Test Case Summary
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Chip 
                        label={`Total: ${generatedTests.length}`} 
                        color="primary" 
                        variant="outlined" 
                      />
                      <Chip 
                        label={`Positive: ${generatedTests.filter((t: any) => t.test_type === 'positive').length}`} 
                        color="success" 
                        variant="outlined" 
                      />
                      <Chip 
                        label={`Negative: ${generatedTests.filter((t: any) => t.test_type === 'negative').length}`} 
                        color="error" 
                        variant="outlined" 
                      />
                      <Chip 
                        label={`Edge: ${generatedTests.filter((t: any) => t.test_type === 'edge').length}`} 
                        color="warning" 
                        variant="outlined" 
                      />
                      <Chip 
                        label={`High Priority: ${generatedTests.filter((t: any) => t.priority === 'High').length}`} 
                        color="error" 
                        size="small"
                      />
                      <Chip 
                        label={`Medium Priority: ${generatedTests.filter((t: any) => t.priority === 'Medium').length}`} 
                        color="warning" 
                        size="small"
                      />
                      <Chip 
                        label={`Low Priority: ${generatedTests.filter((t: any) => t.priority === 'Low').length}`} 
                        color="success" 
                        size="small"
                      />
                    </Box>
                  </Box>

                  {/* Data Grid */}
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
