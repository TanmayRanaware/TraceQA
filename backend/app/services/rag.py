import os
import json
import logging
from typing import List, Dict, Any, Optional
from ..providers.provider_factory import get_provider
from ..config import config
from .pinecone_service import PineconeService

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.llm_provider = get_provider()
        self.embedding_model = config.llm.default_embedding_model
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap
        
        # Initialize Pinecone service
        try:
            self.pinecone_service = PineconeService()
            logger.info("Pinecone service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Pinecone: {str(e)}. Falling back to in-memory storage.")
            self.pinecone_service = None
    
    async def index_text(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Index text for RAG search using Pinecone"""
        try:
            # Chunk the text
            chunks = self._chunk_text(text)
            
            # Generate embeddings for each chunk
            embeddings = self._generate_embeddings(chunks)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{metadata.get('journey', 'unknown')}_{metadata.get('version', 'unknown')}_{i}"
                
                # Filter out null values from metadata for Pinecone compatibility
                clean_metadata = {k: v for k, v in metadata.items() if v is not None}
                
                vector_data = {
                    "id": vector_id,
                    "embedding": embedding,
                    "metadata": {
                        **clean_metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "text": chunk,
                        "text_length": len(chunk)
                    }
                }
                vectors.append(vector_data)
            
            # Store in Pinecone if available, otherwise fallback to memory
            if self.pinecone_service:
                # Use journey as namespace for better organization
                namespace = metadata.get('journey', 'default')
                result = await self.pinecone_service.upsert_vectors(vectors, namespace=namespace)
                
                if result["status"] == "success":
                    logger.info(f"Indexed {len(chunks)} chunks in Pinecone")
                    return {
                        "status": "success",
                        "chunks_indexed": len(chunks),
                        "text_length": len(text),
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap,
                        "storage": "pinecone",
                        "namespace": namespace
                    }
                else:
                    logger.warning(f"Pinecone indexing failed: {result['message']}. Falling back to memory.")
            
            # Fallback to in-memory storage
            return await self._index_in_memory(vectors, text)
            
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Indexing failed: {str(e)}"
            }
    
    async def search(
        self,
        query: str,
        top_k: int = None,
        metadata_filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search indexed text using RAG with Pinecone"""
        try:
            top_k = top_k or config.top_k
            
            # Generate embedding for query
            query_embedding = self._generate_embeddings([query])
            if not query_embedding:
                return []
            
            # Search using Pinecone if available
            if self.pinecone_service:
                # Convert metadata filter to Pinecone format
                pinecone_filter = self._convert_metadata_filter(metadata_filter)
                
                # Use journey as namespace if specified
                namespace = metadata_filter.get('journey', 'default') if metadata_filter else None
                
                search_results = await self.pinecone_service.search_vectors(
                    query_embedding[0],
                    top_k=top_k,
                    namespace=namespace,
                    filter=pinecone_filter
                )
                
                # Format results for consistency
                formatted_results = []
                for result in search_results:
                    formatted_results.append({
                        "text": result["metadata"].get("text", ""),
                        "metadata": result["metadata"],
                        "score": result["score"]
                    })
                
                logger.info(f"Found {len(formatted_results)} results using Pinecone")
                return formatted_results
            
            # Fallback to in-memory search
            return await self._search_in_memory(query_embedding[0], top_k, metadata_filter)
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Rerank search results using LLM"""
        try:
            top_k = top_k or config.top_k
            
            if not candidates:
                return []
            
            # Use LLM to rerank results
            reranked = await self.llm_provider.rerank(
                query=query,
                candidates=[c.get('text', '') for c in candidates],
                model=config.llm.default_model
            )
            
            # Apply reranking to results
            reranked_results = []
            for rank in reranked:
                if rank < len(candidates):
                    reranked_results.append(candidates[rank])
            
            return reranked_results[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            return candidates[:top_k]
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            embeddings = self.llm_provider.embed(
                texts=texts,
                model=self.embedding_model
            )
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            # Return dummy embeddings as fallback
            return [[0.0] * 768 for _ in texts]
    
    def _convert_metadata_filter(self, metadata_filter: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata filter to Pinecone filter format"""
        if not metadata_filter:
            return {}
        
        pinecone_filter = {}
        
        for key, value in metadata_filter.items():
            if isinstance(value, dict) and '$in' in value:
                # List inclusion filter
                pinecone_filter[key] = {"$in": value['$in']}
            else:
                # Exact match filter
                pinecone_filter[key] = value
        
        return pinecone_filter
    
    async def _index_in_memory(self, vectors: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        """Fallback in-memory indexing"""
        if not hasattr(self, '_chunk_store'):
            self._chunk_store = []
        
        self._chunk_store.extend(vectors)
        
        logger.info(f"Indexed {len(vectors)} chunks in memory (fallback)")
        return {
            "status": "success",
            "chunks_indexed": len(vectors),
            "text_length": len(text),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "storage": "memory",
            "warning": "Pinecone unavailable, using in-memory storage"
        }
    
    async def _search_in_memory(
        self,
        query_embedding: List[float],
        top_k: int,
        metadata_filter: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Fallback in-memory search"""
        if not hasattr(self, '_chunk_store') or not self._chunk_store:
            return []
        
        # Filter chunks by metadata if specified
        candidate_chunks = self._chunk_store
        if metadata_filter:
            candidate_chunks = self._filter_chunks_by_metadata(
                self._chunk_store,
                metadata_filter
            )
        
        if not candidate_chunks:
            return []
        
        # Calculate cosine similarity
        similarities = []
        for chunk in candidate_chunks:
            similarity = self._cosine_similarity(
                query_embedding,
                chunk.get('embedding', [])
            )
            similarities.append((similarity, chunk))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for similarity, chunk in similarities[:top_k]:
            results.append({
                "text": chunk.get('metadata', {}).get('text', ''),
                "metadata": chunk.get('metadata', {}),
                "score": similarity
            })
        
        return results
    
    def _filter_chunks_by_metadata(
        self,
        chunks: List[Dict[str, Any]],
        metadata_filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter chunks based on metadata criteria"""
        filtered_chunks = []
        
        for chunk in chunks:
            chunk_metadata = chunk.get('metadata', {})
            matches_filter = True
            
            for key, value in metadata_filter.items():
                if key not in chunk_metadata:
                    matches_filter = False
                    break
                
                chunk_value = chunk_metadata[key]
                
                # Handle different filter types
                if isinstance(value, dict) and '$in' in value:
                    # List inclusion filter
                    if chunk_value not in value['$in']:
                        matches_filter = False
                        break
                elif chunk_value != value:
                    # Exact match filter
                    matches_filter = False
                    break
            
            if matches_filter:
                filtered_chunks.append(chunk)
        
        return filtered_chunks
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        
        # Avoid division by zero
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    async def get_vector_db_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        if self.pinecone_service:
            return await self.pinecone_service.get_index_stats()
        else:
            chunk_count = len(getattr(self, '_chunk_store', []))
            return {
                "status": "success",
                "storage_type": "memory",
                "stats": {
                    "total_vector_count": chunk_count,
                    "dimension": 768,
                    "storage": "in-memory (fallback)"
                }
            }
    
    async def clear_vectors(self, filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """Clear vectors based on filter"""
        if self.pinecone_service and filter:
            return await self.pinecone_service.delete_by_metadata(filter)
        elif self.pinecone_service:
            # Clear all vectors
            return await self.pinecone_service.clear_namespace("default")
        else:
            # Clear in-memory storage
            if hasattr(self, '_chunk_store'):
                self._chunk_store.clear()
            return {
                "status": "success",
                "message": "Cleared in-memory vector storage"
            }


