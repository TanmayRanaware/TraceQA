from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..config import config

router = APIRouter(prefix="/api/config", tags=["configuration"])

@router.get("/")
async def get_config() -> Dict[str, Any]:
    """Get application configuration"""
    return {
        "journeys": [
            {
                "name": journey.name,
                "description": journey.description,
                "color": journey.color
            }
            for journey in config.default_journeys
        ],
        "source_types": [
            {
                "value": st.value,
                "label": st.label,
                "description": st.description,
                "icon": st.icon
            }
            for st in config.default_source_types
        ],
        "supported_formats": config.supported_formats,
        "llm": {
            "default_model": config.llm.default_model,
            "default_embedding_model": config.llm.default_embedding_model,
            "default_temperature": config.llm.default_temperature,
            "max_tokens": config.llm.max_tokens
        },
        "rag": {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k": config.top_k
        },
        "file_limits": {
            "max_file_size_mb": config.max_file_size
        }
    }

@router.get("/journeys")
async def get_journeys() -> Dict[str, Any]:
    """Get available journeys"""
    return {
        "journeys": [
            {
                "name": journey.name,
                "description": journey.description,
                "color": journey.color
            }
            for journey in config.default_journeys
        ]
    }

@router.get("/source-types")
async def get_source_types() -> Dict[str, Any]:
    """Get available source types"""
    return {
        "source_types": [
            {
                "value": st.value,
                "label": st.label,
                "description": st.description,
                "icon": st.icon
            }
            for st in config.default_source_types
        ]
    }

@router.get("/supported-formats")
async def get_supported_formats() -> Dict[str, Any]:
    """Get supported file formats"""
    return {
        "supported_formats": config.supported_formats
    }
