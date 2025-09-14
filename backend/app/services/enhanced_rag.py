import os
import json
import logging
from typing import List, Dict, Any, Optional
from ..providers.provider_factory import get_provider
from ..providers.simple_embedding_provider import SimpleEmbeddingProvider
from ..config import config
from .pinecone_service import PineconeService
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import re

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Enhanced RAG service with LangChain, query expansion, and hybrid search"""
    
    def __init__(self):
        self.llm_provider = get_provider()
        self.embedding_model = config.llm.default_embedding_model
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap
        
        # Initialize enhanced embedding provider
        self.embedding_provider = SimpleEmbeddingProvider(dimension=768)
        
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
        """Index text with enhanced chunking and embeddings"""
        try:
            # Use enhanced text splitting
            chunks = self._chunk_text_enhanced(text)
            
            # Generate embeddings for chunks
            embeddings = self.embedding_provider.embed_texts(chunks)
            
            # Prepare vectors for indexing
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{metadata.get('document_id', 'unknown')}_{i}"
                vector_metadata = {
                    **metadata,
                    "text": chunk,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                }
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": vector_metadata
                })
            
            # Index using Pinecone if available
            if self.pinecone_service:
                result = await self.pinecone_service.upsert_vectors(
                    vectors,
                    namespace=metadata.get('journey', 'default')
                )
                
                if result.get("status") == "success":
                    logger.info(f"Successfully indexed {len(vectors)} chunks using Pinecone")
                    return {
                        "status": "success",
                        "chunks_indexed": len(vectors),
                        "text_length": len(text),
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap,
                        "storage": "pinecone",
                        "namespace": metadata.get('journey', 'default')
                    }
            
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
        """Enhanced search with query expansion and hybrid search"""
        try:
            top_k = top_k or config.top_k
            
            # Query expansion
            expanded_queries = await self._expand_query(query)
            logger.info(f"Generated {len(expanded_queries)} expanded queries")
            
            all_results = []
            seen_chunks = set()
            
            # Search with each expanded query
            for expanded_query in expanded_queries:
                # Generate embedding for query
                query_embedding = self.embedding_provider.embed_texts([expanded_query])
                if not query_embedding:
                    continue
                
                # Semantic search
                semantic_results = await self._semantic_search(
                    query_embedding[0], top_k, metadata_filter
                )
                
                # Keyword search (simple implementation)
                keyword_results = await self._keyword_search(
                    expanded_query, top_k, metadata_filter
                )
                
                # Combine and deduplicate results
                for result in semantic_results + keyword_results:
                    text_hash = hash(result.get('text', '')[:200])
                    if text_hash not in seen_chunks:
                        seen_chunks.add(text_hash)
                        all_results.append(result)
            
            # Rerank results
            reranked_results = await self._rerank_results(query, all_results, top_k)
            
            logger.info(f"Found {len(reranked_results)} results using enhanced search")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {str(e)}")
            return []

    async def _expand_query(self, query: str) -> List[str]:
        """Expand query using LLM to generate related terms and synonyms"""
        try:
            # Create expansion prompt
            expansion_prompt = f"""
            Given the query: "{query}"
            
            Generate 3-5 related search queries that would help find relevant information. 
            Include:
            1. The original query
            2. Synonyms and related terms
            3. Broader and narrower concepts
            4. Alternative phrasings
            
            Return only the queries, one per line, without numbering or explanations.
            """
            
            # Get LLM response
            response = self.llm_provider.generate_text(
                prompt=expansion_prompt,
                temperature=0.3
            )
            
            # Parse queries
            queries = [query]  # Always include original
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and line != query:
                    queries.append(line)
            
            return queries[:5]  # Limit to 5 queries
            
        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return [query]  # Fallback to original query

    async def _semantic_search(
        self,
        query_embedding: List[float],
        top_k: int,
        metadata_filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        try:
            if self.pinecone_service:
                # Convert metadata filter to Pinecone format
                pinecone_filter = self._convert_metadata_filter(metadata_filter)
                
                # Use journey as namespace if specified
                namespace = metadata_filter.get('journey', 'default') if metadata_filter else None
                
                search_results = await self.pinecone_service.search_vectors(
                    query_embedding,
                    top_k=top_k,
                    namespace=namespace,
                    filter=pinecone_filter
                )
                
                # Format results
                formatted_results = []
                for result in search_results:
                    formatted_results.append({
                        "text": result["metadata"].get("text", ""),
                        "metadata": result["metadata"],
                        "score": result["score"],
                        "search_type": "semantic"
                    })
                
                return formatted_results
            
            # Fallback to in-memory search
            return await self._search_in_memory(query_embedding, top_k, metadata_filter)
            
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return []

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        metadata_filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based search"""
        try:
            # Simple keyword matching implementation
            # In a real implementation, you'd use BM25 or similar
            query_words = set(query.lower().split())
            
            # This is a simplified implementation
            # In practice, you'd search through indexed text chunks
            results = []
            
            # For now, return empty results as this would require
            # a more sophisticated keyword index
            logger.info(f"Keyword search for: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {str(e)}")
            return []

    async def _rerank_results(
        self,
        original_query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank results using LLM-based relevance scoring"""
        try:
            if not results:
                return []
            
            # Create reranking prompt
            results_text = "\n".join([
                f"{i+1}. {result.get('text', '')[:200]}..."
                for i, result in enumerate(results[:10])  # Limit to top 10 for reranking
            ])
            
            rerank_prompt = f"""
            Given the original query: "{original_query}"
            
            Rank the following search results by relevance (1 = most relevant):
            
            {results_text}
            
            Return only the ranking numbers in order, separated by commas.
            Example: 3,1,5,2,4
            """
            
            # Get LLM ranking
            response = self.llm_provider.generate_text(
                prompt=rerank_prompt,
                temperature=0.1
            )
            
            # Parse ranking
            try:
                rankings = [int(x.strip()) - 1 for x in response.strip().split(',')]
                reranked = []
                
                for rank in rankings:
                    if 0 <= rank < len(results):
                        reranked.append(results[rank])
                
                return reranked[:top_k]
                
            except (ValueError, IndexError):
                logger.warning("Failed to parse reranking response, using original order")
                return results[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            return results[:top_k]

    def _chunk_text_enhanced(self, text: str) -> List[str]:
        """Enhanced text chunking using LangChain"""
        try:
            # Use the enhanced text splitter from the embedding provider
            if hasattr(self.embedding_provider, 'split_text'):
                return self.embedding_provider.split_text(text)
        except Exception as e:
            logger.warning(f"Enhanced text splitting failed: {e}")
        
        # Fallback to simple chunking
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks

    def _convert_metadata_filter(self, metadata_filter: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata filter to Pinecone filter format"""
        if not metadata_filter:
            return {}
        
        pinecone_filter = {}
        
        for key, value in metadata_filter.items():
            if isinstance(value, dict) and '$in' in value:
                pinecone_filter[key] = {"$in": value['$in']}
            else:
                pinecone_filter[key] = value
        
        return pinecone_filter

    async def _search_in_memory(
        self,
        query_embedding: List[float],
        top_k: int,
        metadata_filter: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fallback in-memory search"""
        if not hasattr(self, '_chunk_store'):
            self._chunk_store = []
        
        # Simple cosine similarity search
        results = []
        for chunk_data in self._chunk_store:
            if self._matches_filter(chunk_data.get('metadata', {}), metadata_filter):
                # Calculate cosine similarity
                similarity = self._cosine_similarity(
                    query_embedding,
                    chunk_data.get('values', [])
                )
                
                results.append({
                    "text": chunk_data.get('metadata', {}).get('text', ''),
                    "metadata": chunk_data.get('metadata', {}),
                    "score": similarity,
                    "search_type": "semantic"
                })
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches the filter"""
        if not filter_dict:
            return True
        
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        
        return True

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        import numpy as np
        
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

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
