import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Search,
  Description,
  Timeline,
  FactCheck,
  Upload,
  History,
  CheckCircle,
  Warning,
  Error,
  Schedule,
} from '@mui/icons-material';
import axios from 'axios';
import { useConfig } from '../contexts/ConfigContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// Add proper types for fact check results
type EvidenceAnalysis = {
  strength?: 'strong' | 'moderate' | 'weak' | 'very_weak';
  confidence?: number;
  sources?: number;
  total_evidence?: number;
};

type FactCheckResults = {
  journey: string;
  claim: string;
  evidence: Array<{
    chunk: string;
    metadata: any;
    score: number;
    relevance: string;
  }>;
  evidence_analysis: EvidenceAnalysis;
};

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`requirements-tabpanel-${index}`}
      aria-labelledby={`requirements-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Requirements: React.FC = () => {
  const { config } = useConfig();
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedJourney, setSelectedJourney] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [timelineData, setTimelineData] = useState([]);
  const [factCheckClaim, setFactCheckClaim] = useState('');
  const [factCheckResults, setFactCheckResults] = useState<FactCheckResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get journeys and source types from configuration
  const journeys = config?.journeys.map(j => j.name) || [];
  const sourceTypes = config?.source_types.map(st => st.value) || [];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || !selectedJourney) return;

    try {
      setLoading(true);
      const response = await axios.post('/requirements/search', {
        journey: selectedJourney,
        query: searchQuery,
        top_k: 10,
      });
      setSearchResults(response.data.results);
    } catch (err) {
      setError('Search failed');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFactCheck = async () => {
    if (!factCheckClaim.trim() || !selectedJourney) return;

    try {
      setLoading(true);
      const response = await axios.post('/requirements/fact-check', {
        journey: selectedJourney,
        claim: factCheckClaim,
      });
      setFactCheckResults(response.data);
    } catch (err) {
      setError('Fact-check failed');
      console.error('Fact-check error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTimelineFetch = async () => {
    if (!selectedJourney) return;

    try {
      setLoading(true);
      const response = await axios.get(`/requirements/timeline/${encodeURIComponent(selectedJourney)}`);
      setTimelineData(response.data.timeline || []);
    } catch (err) {
      setError('Failed to fetch timeline');
      console.error('Timeline error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Set default journey when config loads
  useEffect(() => {
    if (config?.journeys.length && !selectedJourney) {
      setSelectedJourney(config.journeys[0].name);
    }
  }, [config, selectedJourney]);

  if (!config) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading configuration...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Description color="primary" />
        Requirements Management
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
            <Box sx={{ flex: '1 1 300px', minWidth: '250px' }}>
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
            </Box>
            <Box sx={{ flex: '2 1 400px', minWidth: '300px' }}>
              <TextField
                fullWidth
                label="Search Requirements"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter your search query..."
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </Box>
            <Box sx={{ flex: '0 1 150px', minWidth: '120px' }}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleSearch}
                disabled={!searchQuery.trim() || !selectedJourney}
                startIcon={<Search />}
              >
                Search
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Search Results" icon={<Search />} />
        <Tab label="Timeline" icon={<Timeline />} />
        <Tab label="Fact Check" icon={<FactCheck />} />
      </Tabs>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Search Results for "{searchQuery}"
        </Typography>
        
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        {searchResults.length > 0 ? (
          <List>
            {searchResults.map((result: any, index: number) => (
              <Paper key={index} sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Score: {(result.score * 100).toFixed(1)}%
                  </Typography>
                  <Chip
                    label={result.metadata?.source_type || 'Unknown'}
                    size="small"
                    variant="outlined"
                  />
                </Box>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  {result.text}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Source: {result.metadata?.document_uri || 'Unknown'}
                </Typography>
              </Paper>
            ))}
          </List>
        ) : (
          <Typography color="text.secondary">
            No search results found. Try a different query or journey.
          </Typography>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="h6">
            Timeline for {selectedJourney}
          </Typography>
          <Button
            variant="outlined"
            onClick={handleTimelineFetch}
            startIcon={<History />}
          >
            Refresh Timeline
          </Button>
        </Box>
        
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        {timelineData.length > 0 ? (
          <List>
            {timelineData.map((item: any, index: number) => (
              <Paper key={index} sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    {item.version}
                  </Typography>
                  <Chip
                    label={item.source_type}
                    size="small"
                    color="primary"
                  />
                  <Typography variant="caption" color="text.secondary">
                    {new Date(item.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {item.summary}
                </Typography>
              </Paper>
            ))}
          </List>
        ) : (
          <Typography color="text.secondary">
            No timeline data available. Click "Refresh Timeline" to load data.
          </Typography>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Fact Check Claims
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
          <Box sx={{ flex: '2 1 500px', minWidth: '400px' }}>
            <TextField
              fullWidth
              label="Claim to Fact-Check"
              value={factCheckClaim}
              onChange={(e) => setFactCheckClaim(e.target.value)}
              placeholder="Enter a claim to verify against requirements..."
              multiline
              rows={3}
            />
          </Box>
          <Box sx={{ flex: '1 1 200px', minWidth: '150px' }}>
            <Button
              fullWidth
              variant="contained"
              onClick={handleFactCheck}
              disabled={!factCheckClaim.trim() || !selectedJourney}
              startIcon={<FactCheck />}
              sx={{ height: '100%' }}
            >
              Fact Check
            </Button>
          </Box>
        </Box>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {factCheckResults && (
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Fact Check Results
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Claim: {factCheckClaim}
                </Typography>
                <Chip
                  label={`Evidence Strength: ${factCheckResults.evidence_analysis?.strength ?? 'n/a'}`}
                  color={factCheckResults.evidence_analysis?.strength === 'strong' ? 'success' : 'warning'}
                  sx={{ mr: 1 }}
                />
                <Chip
                  label={`Confidence: ${((factCheckResults.evidence_analysis?.confidence ?? 0) * 100).toFixed(1)}%`}
                  variant="outlined"
                />
              </Box>
              
              <Typography variant="h6" sx={{ mb: 2 }}>
                Evidence Sources
              </Typography>
              
              {factCheckResults.evidence?.map((evidence: any, index: number) => (
                <Paper key={index} sx={{ p: 2, mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="body2">
                      Relevance Score: {(evidence.score * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <Typography variant="body2">
                    {evidence.text}
                  </Typography>
                </Paper>
              ))}
            </CardContent>
          </Card>
        )}
      </TabPanel>

      <Typography variant="body2" color="text.secondary" sx={{ mt: 4, textAlign: 'center' }}>
        Upload FSDs, addendums, annexures, or other requirement documents
      </Typography>
    </Box>
  );
};

export default Requirements;
