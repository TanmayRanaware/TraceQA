import hashlib
import random
import numpy as np
from typing import List
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)

class SimpleEmbeddingProvider:
    """Enhanced embedding provider with LangChain and semantic embeddings"""
    
    def __init__(self, dimension: int = 768, model_name: str = "all-mpnet-base-v2"):
        self.dimension = dimension
        self.model_name = model_name
        self.embedding_model = None
        self.text_splitter = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the embedding model and text splitter"""
        try:
            # Initialize HuggingFace embeddings via LangChain
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={'device': 'cpu'},  # Use CPU to avoid GPU issues
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # Initialize advanced text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            logger.info(f"Initialized LangChain embedding model: {self.model_name}")
            logger.info(f"Embedding dimension: {self.embedding_model.client.get_sentence_embedding_dimension()}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize LangChain models: {e}. Using fallback.")
            self.embedding_model = None
            self.text_splitter = None
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate semantic embeddings for texts using LangChain"""
        if self.embedding_model is not None:
            try:
                # Use LangChain embeddings
                embeddings = self.embedding_model.embed_documents(texts)
                logger.info(f"Generated {len(embeddings)} semantic embeddings using LangChain")
                return embeddings
            except Exception as e:
                logger.warning(f"LangChain embedding failed: {e}. Using fallback.")
        
        # Fallback to improved hash-based embeddings
        return self._generate_fallback_embeddings(texts)
    
    def split_text(self, text: str) -> List[str]:
        """Split text using LangChain's advanced text splitter"""
        if self.text_splitter is not None:
            try:
                # Create a Document object for LangChain
                doc = Document(page_content=text)
                chunks = self.text_splitter.split_documents([doc])
                return [chunk.page_content for chunk in chunks]
            except Exception as e:
                logger.warning(f"LangChain text splitting failed: {e}. Using simple splitting.")
        
        # Fallback to simple splitting
        return self._simple_text_split(text)
    
    def _simple_text_split(self, text: str) -> List[str]:
        """Simple text splitting fallback"""
        if len(text) <= 1000:
            return [text]
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + 1000
            if end < len(text):
                # Try to break at sentence boundary
                for i in range(end, max(start + 500, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - 200  # 200 character overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate improved hash-based embeddings as fallback"""
        embeddings = []
        for text in texts:
            # Create multiple hash-based features for better representation
            text_lower = text.lower()
            
            # Word-based features
            words = text_lower.split()
            word_hashes = [hash(word) % 1000 for word in words[:50]]  # Limit to 50 words
            
            # Character n-gram features
            char_ngrams = []
            for i in range(len(text_lower) - 2):
                char_ngrams.append(hash(text_lower[i:i+3]) % 1000)
            
            # Combine features
            features = word_hashes + char_ngrams[:100]  # Limit total features
            
            # Generate embedding based on features
            embedding = [0.0] * self.dimension
            for i, feature in enumerate(features):
                if i < self.dimension:
                    # Use feature value to influence embedding
                    random.seed(feature)
                    embedding[i] = random.uniform(-1, 1)
            
            # Normalize embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [x / norm for x in embedding]
            
            embeddings.append(embedding)
        
        logger.info(f"Generated {len(embeddings)} fallback embeddings")
        return embeddings
    
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embed_texts([text])[0]
