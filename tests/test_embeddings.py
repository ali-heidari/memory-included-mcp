"""Unit tests for embeddings functionality"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from mcp_server.embeddings import generate_embedding, deserialize_embedding, cosine_similarity


class TestEmbeddings:
    """Test embedding operations"""

    @patch('mcp_server.embeddings.SentenceTransformer')
    def test_generate_embedding(self, mock_transformer_class):
        """Test generating embeddings from text"""
        # Mock the transformer
        mock_model = MagicMock()
        mock_transformer_class.return_value = mock_model

        # Mock embedding generation
        test_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_model.encode.return_value = test_embedding

        # Test embedding generation
        text = "Test text for embedding"
        result = generate_embedding(text)

        # Verify
        mock_transformer_class.assert_called_once_with('all-MiniLM-L6-v2')
        mock_model.encode.assert_called_once_with(text)

        # Verify result can be deserialized back
        deserialized = deserialize_embedding(result)
        np.testing.assert_array_equal(deserialized, test_embedding)

    def test_deserialize_embedding(self):
        """Test deserializing embeddings from bytes"""
        # Create test embedding
        original_embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)

        # Serialize
        import pickle
        serialized = pickle.dumps(original_embedding)

        # Deserialize
        result = deserialize_embedding(serialized)

        # Verify
        np.testing.assert_array_equal(result, original_embedding)
        assert result.dtype == np.float32

    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        # Test identical vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)

        # Test orthogonal vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0)

        # Test opposite vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(-1.0)

        # Test similar vectors
        vec1 = np.array([1.0, 0.1, 0.0])
        vec2 = np.array([1.0, 0.0, 0.1])
        similarity = cosine_similarity(vec1, vec2)
        assert similarity > 0.8  # Should be high similarity

    def test_cosine_similarity_normalized(self):
        """Test that cosine similarity works with non-normalized vectors"""
        vec1 = np.array([3.0, 4.0])  # Magnitude 5
        vec2 = np.array([3.0, 4.0])  # Same vector

        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vectors"""
        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 2.0, 3.0])

        # Cosine similarity is undefined for zero vectors, should return 0
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    @patch('mcp_server.embeddings.generate_embedding')
    @patch('mcp_server.embeddings.deserialize_embedding')
    @patch('mcp_server.database.Database')
    def test_search_similar_embeddings(self, mock_db_class, mock_deserialize, mock_generate):
        """Test searching for similar embeddings"""
        from mcp_server.embeddings import search_similar_embeddings

        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        # Mock embeddings
        query_embedding = np.array([1.0, 0.0, 0.0])
        stored_embedding1 = np.array([0.9, 0.1, 0.0])  # Similar
        stored_embedding2 = np.array([0.0, 1.0, 0.0])  # Different

        mock_generate.return_value = query_embedding
        mock_deserialize.side_effect = [stored_embedding1, stored_embedding2]

        # Mock stored memories
        mock_memory1 = MagicMock()
        mock_memory1.id = "mem1"
        mock_memory1.vector_embedding = b"embedding1"

        mock_memory2 = MagicMock()
        mock_memory2.id = "mem2"
        mock_memory2.vector_embedding = b"embedding2"

        mock_db.get_all_embeddings.return_value = [mock_memory1, mock_memory2]

        # Test search
        results = search_similar_embeddings("test_user", "query text", limit=5)

        # Verify
        assert len(results) == 2
        # Results should be sorted by similarity (highest first)
        assert results[0][0] > results[1][0]  # First similarity > second similarity