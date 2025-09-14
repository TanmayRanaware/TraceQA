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
  answer?: string;
  confidence?: number;
  sources_used?: number;
  evidence: Array<{
    text: string;
    metadata: any;
    score: number;
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
  
  // Dynamic journey state
  const [journeys, setJourneys] = useState<string[]>([]);
  const [journeysLoading, setJourneysLoading] = useState(true);

  // Get source types from configuration
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
      console.log('Timeline API response:', response.data);
      // Handle nested timeline structure
      const timeline = response.data.timeline?.timeline || response.data.timeline || [];
      console.log('Processed timeline data:', timeline);
      setTimelineData(timeline);
    } catch (err) {
      setError('Failed to fetch timeline');
      console.error('Timeline error:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshJourneys = async () => {
    try {
      setJourneysLoading(true);
      // Fetch only journeys that have uploaded documents
      const response = await axios.get('/requirements/versions');
      const journeysWithDocs = response.data.versions.map((v: any) => v.journey);
      setJourneys(journeysWithDocs);
    } catch (err) {
      console.error('Failed to refresh journeys:', err);
    } finally {
      setJourneysLoading(false);
    }
  };

  // Fetch journeys dynamically from API - only those with uploaded documents
  useEffect(() => {
    const fetchJourneys = async () => {
      try {
        setJourneysLoading(true);
        // Fetch only journeys that have uploaded documents
        const response = await axios.get('/requirements/versions');
        const journeysWithDocs = response.data.versions.map((v: any) => v.journey);
        setJourneys(journeysWithDocs);
        
        // Don't auto-select first journey - let user choose
      } catch (err) {
        console.error('Failed to fetch journeys:', err);
        // Fallback to config journeys if API fails
        if (config?.journeys.length) {
          const fallbackJourneys = config.journeys.map(j => j.name);
          setJourneys(fallbackJourneys);
          // Don't auto-select first journey - let user choose
        }
      } finally {
        setJourneysLoading(false);
      }
    };

    fetchJourneys();
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
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                <FormControl fullWidth>
                  <InputLabel id="journey-select-label" shrink={true}>Journey</InputLabel>
                  <Select
                    labelId="journey-select-label"
                    value={selectedJourney}
                    label="Journey"
                    onChange={(e: SelectChangeEvent) => setSelectedJourney(e.target.value)}
                    disabled={journeysLoading}
                    displayEmpty
                    renderValue={(selected) => {
                      if (!selected) {
                        return <em style={{ color: '#999' }}>Select Journey</em>;
                      }
                      return selected;
                    }}
                    sx={{
                      '& .MuiSelect-select': {
                        display: 'flex',
                        alignItems: 'center',
                        minHeight: '1.4375em'
                      }
                    }}
                  >
                    <MenuItem value="" disabled>
                      <em>Select Journey</em>
                    </MenuItem>
                    {journeys.map((journey) => (
                      <MenuItem key={journey} value={journey}>
                        {journey}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={refreshJourneys}
                  disabled={journeysLoading}
                  sx={{ mt: 1, minWidth: 'auto' }}
                >
                  Refresh
                </Button>
              </Box>
              {journeysLoading && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  Loading journeys...
                </Typography>
              )}
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
        <Tab label="Timeline" icon={<Timeline />} />
        <Tab label="Fact Check" icon={<FactCheck />} />
      </Tabs>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}


      <TabPanel value={tabValue} index={0}>
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

      <TabPanel value={tabValue} index={1}>
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
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Question: {factCheckClaim}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Chip
                    label={`Confidence: ${((factCheckResults.confidence ?? 0) * 100).toFixed(1)}%`}
                    color={(factCheckResults.confidence ?? 0) > 0.7 ? 'success' : (factCheckResults.confidence ?? 0) > 0.4 ? 'warning' : 'error'}
                  />
                  <Chip
                    label={`Sources: ${factCheckResults.sources_used ?? 0}`}
                    variant="outlined"
                  />
                </Box>
              </Box>

              {/* Main Answer Section */}
              {factCheckResults.answer && (
                <Paper sx={{ p: 3, mb: 3, backgroundColor: 'primary.main', color: 'primary.contrastText' }}>
                  <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <FactCheck />
                    Answer from Documents
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>
                    {factCheckResults.answer}
                  </Typography>
                </Paper>
              )}
              
              {/* Evidence Sources - Collapsible */}
              {factCheckResults.evidence && factCheckResults.evidence.length > 0 && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Description />
                    Supporting Evidence ({factCheckResults.evidence.length} sources)
                  </Typography>
                  
                  {factCheckResults.evidence.slice(0, 3).map((evidence: any, index: number) => (
                    <Paper key={index} sx={{ p: 2, mb: 2, border: '1px solid', borderColor: 'divider' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Chip
                          label={evidence.metadata?.source_type || 'Unknown'}
                          size="small"
                          variant="outlined"
                        />
                        <Typography variant="caption" color="text.secondary">
                          Version: {evidence.metadata?.version || 'Unknown'}
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ 
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 4,
                        WebkitBoxOrient: 'vertical',
                      }}>
                        {evidence.text}
                      </Typography>
                      {evidence.metadata?.document_uri && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Source: {evidence.metadata.document_uri.split('/').pop()}
                        </Typography>
                      )}
                    </Paper>
                  ))}

                  {factCheckResults.evidence.length > 3 && (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 1 }}>
                      ... and {factCheckResults.evidence.length - 3} more evidence sources
                    </Typography>
                  )}
                </Box>
              )}
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
