"""Vector embedding generation and semantic search"""

import pickle
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

# Lazy load embedding model to save startup time
_embedding_model = None


def get_embedding_model():
    """Lazy load sentence-transformers model"""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from config import EMBEDDING_MODEL_NAME

            logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
            return None
    return _embedding_model


def generate_embedding(text: str) -> bytes:
    """Generate vector embedding for text

    Args:
        text: Text to embed

    Returns:
        Serialized numpy array as bytes
    """
    model = get_embedding_model()
    if model is None:
        return None

    try:
        # Generate embedding (returns numpy array)
        embedding = model.encode(text, convert_to_numpy=True)

        # Serialize to bytes for storage in BLOB
        embedding_bytes = pickle.dumps(embedding)
        return embedding_bytes
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def deserialize_embedding(embedding_bytes: bytes) -> np.ndarray:
    """Deserialize embedding from bytes

    Args:
        embedding_bytes: Serialized numpy array

    Returns:
        Numpy array
    """
    try:
        return pickle.loads(embedding_bytes)
    except Exception as e:
        logger.error(f"Error deserializing embedding: {e}")
        return None


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Similarity score between 0 and 1
    """
    # Normalize vectors
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

    # Compute cosine similarity
    similarity = np.dot(vec1_norm, vec2_norm)

    # Clamp to [0, 1] range
    return float(max(0.0, min(1.0, similarity)))


def search_similar_embeddings(
    query_embedding_bytes: bytes,
    stored_embeddings: List[Tuple[str, bytes]],
    top_k: int = 5,
    threshold: float = 0.3,
) -> List[Tuple[str, float]]:
    """Find similar embeddings using cosine similarity

    Args:
        query_embedding_bytes: Serialized query embedding
        stored_embeddings: List of (memory_id, embedding_bytes) tuples
        top_k: Number of results to return
        threshold: Minimum similarity score

    Returns:
        List of (memory_id, similarity_score) tuples, sorted by similarity
    """
    if query_embedding_bytes is None:
        return []

    try:
        query_embedding = deserialize_embedding(query_embedding_bytes)
        if query_embedding is None:
            return []

        similarities = []

        for memory_id, stored_embedding_bytes in stored_embeddings:
            if stored_embedding_bytes is None:
                continue

            stored_embedding = deserialize_embedding(stored_embedding_bytes)
            if stored_embedding is None:
                continue

            # Calculate similarity
            sim_score = cosine_similarity(query_embedding, stored_embedding)

            # Only include if above threshold
            if sim_score >= threshold:
                similarities.append((memory_id, sim_score))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top_k results
        return similarities[:top_k]

    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return []
