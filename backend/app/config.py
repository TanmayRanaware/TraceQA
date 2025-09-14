import os
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class LLMConfig:
    """LLM provider configuration"""
    default_model: str = "claude-3-5-haiku-20241022"
    default_embedding_model: str = "text-embedding-3-small"
    default_temperature: float = 0.2
    max_tokens: int = 4000

@dataclass
class JourneyConfig:
    """Journey configuration"""
    name: str
    description: str
    color: str = "primary"

@dataclass
class SourceTypeConfig:
    """Source type configuration"""
    value: str
    label: str
    description: str
    icon: str = "Description"

@dataclass
class AppConfig:
    """Main application configuration"""
    
    # LLM Configuration
    llm: LLMConfig = None
    
    # Default Journeys (can be overridden via environment or config file)
    default_journeys: List[JourneyConfig] = None
    
    # Default Source Types (can be overridden via environment or config file)
    default_source_types: List[SourceTypeConfig] = None
    
    # File Storage
    base_dir: str = os.environ.get("BASE_DIR", "object_store")
    req_versions_dir: str = os.environ.get("REQ_VERSIONS_DIR", "req_versions")
    
    # API Configuration
    max_file_size: int = int(os.environ.get("MAX_FILE_SIZE", "50"))  # MB
    supported_formats: List[str] = None
    
    # RAG Configuration
    chunk_size: int = int(os.environ.get("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.environ.get("CHUNK_OVERLAP", "200"))
    top_k: int = int(os.environ.get("TOP_K", "10"))
    
    def __post_init__(self):
        # Set default LLM config if not provided
        if self.llm is None:
            self.llm = LLMConfig()
        
        # Set default journeys if not provided
        if self.default_journeys is None:
            self.default_journeys = [
                JourneyConfig("Point of Settlement", "Banking settlement and clearing processes", "primary"),
                JourneyConfig("Payment Processing", "Payment transaction workflows", "secondary"),
                JourneyConfig("Account Management", "Customer account operations", "success"),
                JourneyConfig("Risk Management", "Risk assessment and mitigation", "warning"),
                JourneyConfig("Compliance", "Regulatory compliance processes", "info"),
            ]
        
        # Set default source types if not provided
        if self.default_source_types is None:
            self.default_source_types = [
                SourceTypeConfig("fsd", "FSD (Functional Specification Document)", "Primary requirement specification", "Description"),
                SourceTypeConfig("addendum", "Addendum", "Additional requirements or clarifications", "Add"),
                SourceTypeConfig("annexure", "Annexure", "Supporting documentation or appendices", "AttachFile"),
                SourceTypeConfig("email", "Email Communication", "Requirements communicated via email", "Email"),
                SourceTypeConfig("meeting_notes", "Meeting Notes", "Requirements from stakeholder meetings", "EventNote"),
                SourceTypeConfig("change_request", "Change Request", "Formal change request documentation", "ChangeCircle"),
            ]
        
        # Set supported formats if not provided
        if self.supported_formats is None:
            self.supported_formats = ["pdf", "docx", "txt", "md", "rtf"]
    
    @classmethod
    def from_environment(cls) -> 'AppConfig':
        """Create configuration from environment variables"""
        config = cls()
        
        # Override journeys from environment if specified
        journeys_env = os.environ.get("JOURNEYS")
        if journeys_env:
            try:
                journeys_data = eval(journeys_env)  # Parse list of dicts
                config.default_journeys = [JourneyConfig(**j) for j in journeys_data]
            except:
                pass  # Keep defaults if parsing fails
        
        # Override source types from environment if specified
        source_types_env = os.environ.get("SOURCE_TYPES")
        if source_types_env:
            try:
                source_types_data = eval(source_types_env)  # Parse list of dicts
                config.default_source_types = [SourceTypeConfig(**st) for st in source_types_data]
            except:
                pass  # Keep defaults if parsing fails
        
        return config
    
    def get_journey_names(self) -> List[str]:
        """Get list of journey names"""
        return [journey.name for journey in self.default_journeys]
    
    def get_source_type_values(self) -> List[str]:
        """Get list of source type values"""
        return [st.value for st in self.default_source_types]
    
    def get_source_type_labels(self) -> List[Dict[str, str]]:
        """Get list of source type labels for UI"""
        return [{"value": st.value, "label": st.label} for st in self.default_source_types]

# Global configuration instance
config = AppConfig.from_environment()
