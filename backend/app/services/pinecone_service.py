import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from ..config import config

logger = logging.getLogger(__name__)

class PineconeService:
    def __init__(self):
        self.api_key = os.environ.get("PINECONE_API_KEY")
        self.environment = os.environ.get("PINECONE_ENVIRONMENT", "gcp-starter")
        self.index_name = os.environ.get("PINECONE_INDEX_NAME", "traceq")
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Ensure the Pinecone index exists, create if it doesn't"""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                
                # Create index with appropriate configuration
                self.pc.create_index(
                    name=self.index_name,
                    dimension=768,  # Gemini embedding-001 dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
                # Wait for index to be ready
                import time
                while not self.pc.describe_index(self.index_name).status["ready"]:
                    time.sleep(1)
                    logger.info("Waiting for index to be ready...")
                
                logger.info(f"Index {self.index_name} created successfully")
            
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to create/connect to Pinecone index: {str(e)}")
            raise
    
    async def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = None
    ) -> Dict[str, Any]:
        """Upsert vectors to Pinecone index"""
        try:
            if not self.index:
                raise Exception("Pinecone index not initialized")
            
            # Prepare vectors for Pinecone
            pinecone_vectors = []
            for vector_data in vectors:
                pinecone_vector = {
                    "id": vector_data["id"],
                    "values": vector_data["embedding"],
                    "metadata": vector_data["metadata"]
                }
                pinecone_vectors.append(pinecone_vector)
            
            # Upsert to Pinecone
            result = self.index.upsert(
                vectors=pinecone_vectors,
                namespace=namespace
            )
            
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone")
            return {
                "status": "success",
                "upserted_count": result.upserted_count,
                "message": f"Successfully upserted {result.upserted_count} vectors"
            }
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to upsert vectors: {str(e)}"
            }
    
    async def search_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: str = None,
        filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in Pinecone"""
        try:
            if not self.index:
                raise Exception("Pinecone index not initialized")
            
            # Perform vector search
            search_result = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=True
            )
            
            # Format results
            results = []
            for match in search_result.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            logger.info(f"Found {len(results)} similar vectors")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {str(e)}")
            return []
    
    async def delete_vectors(
        self,
        vector_ids: List[str],
        namespace: str = None
    ) -> Dict[str, Any]:
        """Delete vectors from Pinecone index"""
        try:
            if not self.index:
                raise Exception("Pinecone index not initialized")
            
            # Delete vectors
            result = self.index.delete(
                ids=vector_ids,
                namespace=namespace
            )
            
            logger.info(f"Deleted {len(vector_ids)} vectors from Pinecone")
            return {
                "status": "success",
                "deleted_count": len(vector_ids),
                "message": f"Successfully deleted {len(vector_ids)} vectors"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to delete vectors: {str(e)}"
            }
    
    async def delete_by_metadata(
        self,
        filter: Dict[str, Any],
        namespace: str = None
    ) -> Dict[str, Any]:
        """Delete vectors by metadata filter"""
        try:
            if not self.index:
                raise Exception("Pinecone index not initialized")
            
            # First, search for vectors matching the filter
            search_result = self.index.query(
                vector=[0.0] * 768,  # Dummy vector for metadata-only search
                top_k=10000,  # Large number to get all matches
                namespace=namespace,
                filter=filter,
                include_metadata=False
            )
            
            if not search_result.matches:
                return {
                    "status": "success",
                    "deleted_count": 0,
                    "message": "No vectors found matching the filter"
                }
            
            # Extract IDs and delete
            vector_ids = [match.id for match in search_result.matches]
            return await self.delete_vectors(vector_ids, namespace)
            
        except Exception as e:
            logger.error(f"Failed to delete by metadata: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to delete by metadata: {str(e)}"
            }
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index"""
        try:
            if not self.index:
                raise Exception("Pinecone index not initialized")
            
            stats = self.index.describe_index_stats()
            
            # Convert namespaces to serializable format
            serializable_namespaces = {}
            if hasattr(stats, 'namespaces') and stats.namespaces:
                for namespace, ns_stats in stats.namespaces.items():
                    serializable_namespaces[namespace] = {
                        "vector_count": ns_stats.vector_count
                    }
            
            return {
                "status": "success",
                "storage_type": "pinecone",
                "stats": {
                    "total_vector_count": stats.total_vector_count,
                    "dimension": stats.dimension,
                    "index_fullness": stats.index_fullness,
                    "namespaces": serializable_namespaces
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get index stats: {str(e)}"
            }
    
    async def clear_namespace(self, namespace: str) -> Dict[str, Any]:
        """Clear all vectors in a specific namespace"""
        try:
            if not self.index:
                raise Exception("Pinecone index not initialized")
            
            # Delete all vectors in namespace
            result = self.index.delete(
                delete_all=True,
                namespace=namespace
            )
            
            logger.info(f"Cleared namespace: {namespace}")
            return {
                "status": "success",
                "message": f"Successfully cleared namespace: {namespace}"
            }
            
        except Exception as e:
            logger.error(f"Failed to clear namespace: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to clear namespace: {str(e)}"
            }
