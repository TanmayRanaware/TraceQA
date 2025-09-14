import hashlib
import random
from typing import List

class SimpleEmbeddingProvider:
    """Simple embedding provider that generates deterministic embeddings without external APIs"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate simple hash-based embeddings for texts"""
        embeddings = []
        for text in texts:
            # Create a deterministic seed from text hash
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            seed = int(text_hash[:8], 16)
            random.seed(seed)
            
            # Generate a deterministic vector
            embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
            embeddings.append(embedding)
        
        return embeddings
    
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return self.embed_texts([text])[0]
