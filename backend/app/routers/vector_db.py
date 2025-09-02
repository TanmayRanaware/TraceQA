from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from ..services.rag import RAGService

router = APIRouter(prefix="/api/vector-db", tags=["vector-database"])

@router.get("/stats")
async def get_vector_db_stats() -> Dict[str, Any]:
    """Get vector database statistics"""
    try:
        rag_service = RAGService()
        stats = await rag_service.get_vector_db_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vector DB stats: {str(e)}")

@router.delete("/clear")
async def clear_vectors(filter: Dict[str, Any] = None) -> Dict[str, Any]:
    """Clear vectors based on filter"""
    try:
        rag_service = RAGService()
        result = await rag_service.clear_vectors(filter)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear vectors: {str(e)}")

@router.delete("/clear-journey/{journey}")
async def clear_journey_vectors(journey: str) -> Dict[str, Any]:
    """Clear all vectors for a specific journey"""
    try:
        rag_service = RAGService()
        filter = {"journey": journey}
        result = await rag_service.clear_vectors(filter)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear journey vectors: {str(e)}")

@router.delete("/clear-source-type/{source_type}")
async def clear_source_type_vectors(source_type: str) -> Dict[str, Any]:
    """Clear all vectors for a specific source type"""
    try:
        rag_service = RAGService()
        filter = {"source_type": source_type}
        result = await rag_service.clear_vectors(filter)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear source type vectors: {str(e)}")

@router.post("/reindex")
async def reindex_documents(journey: str = None, source_type: str = None) -> Dict[str, Any]:
    """Reindex documents (placeholder for future implementation)"""
    try:
        # This would typically involve:
        # 1. Reading all documents from storage
        # 2. Clearing existing vectors
        # 3. Re-indexing all documents
        
        return {
            "status": "success",
            "message": "Reindexing is not yet implemented. This endpoint is a placeholder.",
            "journey": journey,
            "source_type": source_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reindex: {str(e)}")

@router.get("/health")
async def vector_db_health() -> Dict[str, Any]:
    """Check vector database health"""
    try:
        rag_service = RAGService()
        stats = await rag_service.get_vector_db_stats()
        
        if stats["status"] == "success":
            return {
                "status": "healthy",
                "storage_type": stats.get("storage_type", "unknown"),
                "vector_count": stats.get("stats", {}).get("total_vector_count", 0)
            }
        else:
            return {
                "status": "unhealthy",
                "error": stats.get("message", "Unknown error")
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
