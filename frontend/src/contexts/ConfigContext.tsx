import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

export interface Journey {
  name: string;
  description: string;
  color: string;
}

export interface SourceType {
  value: string;
  label: string;
  description: string;
  icon: string;
}

export interface LLMConfig {
  default_model: string;
  default_embedding_model: string;
  default_temperature: number;
  max_tokens: number;
}

export interface RAGConfig {
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
}

export interface AppConfig {
  journeys: Journey[];
  source_types: SourceType[];
  supported_formats: string[];
  llm: LLMConfig;
  rag: RAGConfig;
  file_limits: {
    max_file_size_mb: number;
  };
}

interface ConfigContextType {
  config: AppConfig | null;
  loading: boolean;
  error: string | null;
  refreshConfig: () => Promise<void>;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};

interface ConfigProviderProps {
  children: ReactNode;
}

export const ConfigProvider: React.FC<ConfigProviderProps> = ({ children }) => {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get('/api/config/');
      setConfig(response.data);
    } catch (err) {
      console.error('Failed to fetch configuration:', err);
      setError('Failed to load configuration');
      
      // Set fallback configuration
      setConfig({
        journeys: [
          { name: 'Point of Settlement', description: 'Banking settlement and clearing processes', color: 'primary' },
          { name: 'Payment Processing', description: 'Payment transaction workflows', color: 'secondary' },
          { name: 'Account Management', description: 'Customer account operations', color: 'success' },
        ],
        source_types: [
          { value: 'fsd', label: 'FSD (Functional Specification Document)', description: 'Primary requirement specification', icon: 'Description' },
          { value: 'addendum', label: 'Addendum', description: 'Additional requirements or clarifications', icon: 'Add' },
          { value: 'annexure', label: 'Annexure', description: 'Supporting documentation or appendices', icon: 'AttachFile' },
          { value: 'email', label: 'Email Communication', description: 'Requirements communicated via email', icon: 'Email' },
        ],
        supported_formats: ['pdf', 'docx', 'txt', 'md', 'rtf'],
        llm: {
          default_model: 'claude-3-5-haiku-20241022',
          default_embedding_model: 'text-embedding-3-small',
          default_temperature: 0.2,
          max_tokens: 4000,
        },
        rag: {
          chunk_size: 1000,
          chunk_overlap: 200,
          top_k: 10,
        },
        file_limits: {
          max_file_size_mb: 50,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  const refreshConfig = async () => {
    await fetchConfig();
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const value: ConfigContextType = {
    config,
    loading,
    error,
    refreshConfig,
  };

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  );
};
