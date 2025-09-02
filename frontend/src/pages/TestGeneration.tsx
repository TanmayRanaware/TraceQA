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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  BugReport,
  PlayArrow,
  Schedule,
  CheckCircle,
  Warning,
  ExpandMore,
  Description,
  Settings,
} from '@mui/icons-material';
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
  const [showAdvanced, setShowAdvanced] = useState(false);

  const journeys = ['Point of Settlement', 'Payment Processing', 'Account Management'];
  const providers = ['gemini', 'ollama', 'openai'];
  const models = {
    gemini: ['gemini-2.0-flash', 'gemini-1.5-pro'],
    ollama: ['llama3.1:8b-instruct', 'llama3.1:70b-instruct', 'mistral:7b-instruct'],
    openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
  };

  const handleGenerateTests = async () => {
    if (!selectedJourney) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/tests/generate', {
        journey: selectedJourney,
        max_cases: maxCases,
        context_top_k: contextTopK,
        provider: selectedProvider || undefined,
        model: selectedModel || undefined,
      });
      
      setGeneratedTests(response.data.tests);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate tests');
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
              <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <BugReport />
                Generated Test Cases
                {generatedTests.length > 0 && (
                  <Chip label={generatedTests.length} color="primary" size="small" />
                )}
              </Typography>

              {loading && (
                <Box sx={{ mb: 3 }}>
                  <LinearProgress />
                  <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                    Generating test cases using AI...
                  </Typography>
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              {generatedTests.length > 0 ? (
                <List>
                  {generatedTests.map((test: any, index: number) => (
                    <React.Fragment key={index}>
                      <ListItem sx={{ px: 0, py: 2 }}>
                        <ListItemIcon>
                          <BugReport color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ mb: 1 }}>
                              <Typography variant="h6" sx={{ mb: 1 }}>
                                {test.title}
                              </Typography>
                              <Chip
                                label={getTestTypeColor(test.title)}
                                color={getTestTypeColor(test.title) as any}
                                size="small"
                                sx={{ mr: 1 }}
                              />
                              {test.tags?.map((tag: string, tagIndex: number) => (
                                <Chip
                                  key={tagIndex}
                                  label={tag}
                                  variant="outlined"
                                  size="small"
                                  sx={{ mr: 1 }}
                                />
                              ))}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Steps:
                              </Typography>
                              <List dense>
                                {test.steps?.map((step: string, stepIndex: number) => (
                                  <ListItem key={stepIndex} sx={{ py: 0 }}>
                                    <ListItemIcon sx={{ minWidth: 30 }}>
                                      <Typography variant="body2" color="primary">
                                        {stepIndex + 1}.
                                      </Typography>
                                    </ListItemIcon>
                                    <ListItemText primary={step} />
                                  </ListItem>
                                ))}
                              </List>
                              
                              <Typography variant="subtitle2" sx={{ mt: 2, fontWeight: 600 }}>
                                Expected Result:
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {test.expected}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < generatedTests.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
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
