"""API tests for MCP server endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from mcp_server.main import app


class TestAPI:
    """Test API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "embeddings" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    @patch('mcp_server.main.summarize_text')
    @patch('mcp_server.main.generate_embedding')
    @patch('mcp_server.main.Database')
    def test_store_memory_success(self, mock_db_class, mock_generate_embedding, mock_summarize, client):
        """Test successful memory storage"""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.add_memory.return_value = "test_memory_id"

        # Mock summarization
        mock_summarize.return_value = "Summarized content"

        # Mock embedding
        mock_generate_embedding.return_value = b"mock_embedding"

        # Test data
        test_data = {
            "user_id": "test_user",
            "content": "I love dark mode interfaces"
        }

        response = client.post("/store_memory", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_memory_id"
        assert data["summary"] == "Summarized content"
        assert data["status"] == "stored"

        # Verify database was called
        mock_db.add_memory.assert_called_once()

    def test_store_memory_invalid_data(self, client):
        """Test store memory with invalid data"""
        # Missing user_id
        test_data = {
            "content": "Test content"
        }

        response = client.post("/store_memory", json=test_data)
        assert response.status_code == 422  # Validation error

    def test_store_memory_empty_content(self, client):
        """Test store memory with empty content"""
        test_data = {
            "user_id": "test_user",
            "content": ""
        }

        response = client.post("/store_memory", json=test_data)
        assert response.status_code == 422  # Validation error

    @patch('mcp_server.main.search_similar_embeddings')
    @patch('mcp_server.main.Database')
    def test_search_memory_success(self, mock_db_class, mock_search_embeddings, client):
        """Test successful memory search"""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        # Mock search results
        mock_result1 = MagicMock()
        mock_result1.id = "mem1"
        mock_result1.original_text = "Dark mode is great"
        mock_result1.summary = "User likes dark mode"
        mock_result1.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_result2 = MagicMock()
        mock_result2.id = "mem2"
        mock_result2.original_text = "I prefer shortcuts"
        mock_result2.summary = "User likes shortcuts"
        mock_result2.created_at.isoformat.return_value = "2024-01-02T00:00:00"

        mock_search_embeddings.return_value = [
            (0.95, mock_result1),
            (0.87, mock_result2)
        ]

        # Test data
        test_data = {
            "user_id": "test_user",
            "query": "dark mode",
            "limit": 5
        }

        response = client.post("/search_memory", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_found" in data
        assert len(data["results"]) == 2

        # Check first result
        result1 = data["results"][0]
        assert result1["id"] == "mem1"
        assert result1["summary"] == "User likes dark mode"
        assert "similarity" in result1

    def test_search_memory_invalid_data(self, client):
        """Test search memory with invalid data"""
        # Missing user_id
        test_data = {
            "query": "test query"
        }

        response = client.post("/search_memory", json=test_data)
        assert response.status_code == 422  # Validation error

    def test_search_memory_empty_query(self, client):
        """Test search memory with empty query"""
        test_data = {
            "user_id": "test_user",
            "query": ""
        }

        response = client.post("/search_memory", json=test_data)
        assert response.status_code == 422  # Validation error

    @patch('mcp_server.main.Database')
    def test_get_memories_by_user(self, mock_db_class, client):
        """Test getting all memories for a user"""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        # Mock memories
        mock_memory = MagicMock()
        mock_memory.to_dict.return_value = {
            "id": "mem1",
            "user_id": "test_user",
            "original_text": "Test memory",
            "summary": "Test summary",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }

        mock_db.get_all_memories_by_user.return_value = [mock_memory]

        response = client.get("/memories/test_user")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["memories"]) == 1
        assert data["memories"][0]["id"] == "mem1"

    @patch('mcp_server.main.Database')
    def test_delete_memory_success(self, mock_db_class, client):
        """Test successful memory deletion"""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.delete_memory.return_value = True

        response = client.delete("/memories/test_memory_id")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["id"] == "test_memory_id"

        mock_db.delete_memory.assert_called_once_with("test_memory_id")

    @patch('mcp_server.main.Database')
    def test_delete_memory_not_found(self, mock_db_class, client):
        """Test deleting non-existent memory"""
        # Mock database
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.delete_memory.return_value = False

        response = client.delete("/memories/non_existent_id")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_stream_endpoint(self, client):
        """Test SSE streaming endpoint"""
        # This is a basic test - in a real scenario you'd test the streaming
        response = client.get("/stream", stream=True)

        assert response.status_code == 200
        # Check content type for SSE
        assert "text/event-stream" in response.headers.get("content-type", "")

    @patch('mcp_server.main.Database')
    def test_database_error_handling(self, mock_db_class, client):
        """Test error handling when database operations fail"""
        # Mock database to raise exception
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.add_memory.side_effect = Exception("Database error")

        test_data = {
            "user_id": "test_user",
            "content": "Test content"
        }

        response = client.post("/store_memory", json=test_data)

        assert response.status_code == 500
        data = response.json()
        assert "error" in data