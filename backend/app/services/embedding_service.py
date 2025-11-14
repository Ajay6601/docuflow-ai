from sentence_transformers import SentenceTransformer
import numpy as np
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings for semantic search."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model.
        
        all-MiniLM-L6-v2:
        - 384 dimensions
        - Fast and efficient
        - Good for semantic search
        - ~80MB model size
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimensions = 384
        logger.info(f"Embedding model loaded successfully ({self.dimensions} dimensions)")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        try:
            if not text or len(text.strip()) < 10:
                logger.warning("Text too short for embedding generation")
                return None
            
            # Truncate text if too long (model max is typically 512 tokens)
            max_chars = 5000
            if len(text) > max_chars:
                text = text[:max_chars]
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list
            embedding_list = embedding.tolist()
            
            logger.debug(f"Generated embedding with {len(embedding_list)} dimensions")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts (more efficient).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embeddings (same order as input)
        """
        try:
            # Filter out empty texts
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(texts):
                if text and len(text.strip()) >= 10:
                    valid_texts.append(text[:5000])  # Truncate
                    valid_indices.append(i)
            
            if not valid_texts:
                return [None] * len(texts)
            
            # Generate embeddings in batch
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
            
            # Map back to original positions
            result = [None] * len(texts)
            for i, embedding in zip(valid_indices, embeddings):
                result[i] = embedding.tolist()
            
            logger.info(f"Generated {len(valid_texts)} embeddings in batch")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Returns:
            Similarity score between 0 and 1 (1 = identical, 0 = completely different)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            # Convert to 0-1 range
            similarity = (similarity + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0


# Singleton instance
embedding_service = EmbeddingService()