"""Unit tests for database operations"""

import pytest
import tempfile
import os
import sys

# Add the parent directory to the path so we can import mcp_server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mcp_server.database import Database, Conversation, Base
from mcp_server.config import SUMMARY_RULES


class TestDatabase:
    """Test database operations"""

    @pytest.fixture
    def db(self):
        """Create a temporary database for testing"""
        # Create temporary database file
        db_fd, db_path = tempfile.mkstemp()
        db_url = f"sqlite:///{db_path}"

        # Create database instance
        database = Database(db_url)

        yield database

        # Cleanup
        os.close(db_fd)
        os.unlink(db_path)

    def test_database_initialization(self, db):
        """Test database initialization creates tables"""
        # Check that tables were created
        assert db.engine.table_names() == ['conversations']

    def test_add_memory(self, db):
        """Test adding a memory to the database"""
        user_id = "test_user"
        content = "Test memory content"
        summary = "Test summary"

        # Add memory
        memory_id = db.add_memory(user_id, content, summary)

        # Verify it was added
        assert memory_id is not None

        # Retrieve and verify
        memory = db.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.user_id == user_id
        assert memory.original_text == content
        assert memory.summary == summary
        assert memory.message_type == "user"

    def test_get_all_memories_by_user(self, db):
        """Test retrieving all memories for a user"""
        user_id = "test_user"

        # Add multiple memories
        db.add_memory(user_id, "Memory 1", "Summary 1")
        db.add_memory(user_id, "Memory 2", "Summary 2")
        db.add_memory("other_user", "Other memory", "Other summary")

        # Get memories for user
        memories = db.get_all_memories_by_user(user_id)

        # Verify
        assert len(memories) == 2
        assert all(m.user_id == user_id for m in memories)

    def test_get_memory_by_id(self, db):
        """Test retrieving a specific memory by ID"""
        user_id = "test_user"
        content = "Test content"
        summary = "Test summary"

        # Add memory
        memory_id = db.add_memory(user_id, content, summary)

        # Retrieve by ID
        memory = db.get_memory_by_id(memory_id)

        # Verify
        assert memory is not None
        assert memory.id == memory_id
        assert memory.user_id == user_id
        assert memory.original_text == content
        assert memory.summary == summary

    def test_delete_memory(self, db):
        """Test deleting a memory"""
        user_id = "test_user"
        content = "Test content"
        summary = "Test summary"

        # Add memory
        memory_id = db.add_memory(user_id, content, summary)

        # Verify it exists
        assert db.get_memory_by_id(memory_id) is not None

        # Delete memory
        result = db.delete_memory(memory_id)
        assert result is True

        # Verify it's gone
        assert db.get_memory_by_id(memory_id) is None

    def test_search_memories_by_user(self, db):
        """Test searching memories for a user"""
        user_id = "test_user"

        # Add memories with different content
        db.add_memory(user_id, "I love dark mode", "User prefers dark mode")
        db.add_memory(user_id, "I use keyboard shortcuts", "User likes shortcuts")
        db.add_memory(user_id, "Python is great", "User likes Python")
        db.add_memory("other_user", "Other content", "Other summary")

        # Search for "dark"
        results = db.search_memories_by_user(user_id, "dark", limit=5)
        assert len(results) == 1
        assert "dark" in results[0].original_text.lower()

        # Search for "user" (should match all)
        results = db.search_memories_by_user(user_id, "user", limit=5)
        assert len(results) == 3

        # Search for non-existent term
        results = db.search_memories_by_user(user_id, "nonexistent", limit=5)
        assert len(results) == 0

    def test_memory_to_dict(self, db):
        """Test memory object serialization"""
        user_id = "test_user"
        content = "Test content"
        summary = "Test summary"

        # Add memory
        memory_id = db.add_memory(user_id, content, summary)
        memory = db.get_memory_by_id(memory_id)

        # Convert to dict
        memory_dict = memory.to_dict()

        # Verify structure
        assert isinstance(memory_dict, dict)
        assert memory_dict["id"] == memory_id
        assert memory_dict["user_id"] == user_id
        assert memory_dict["original_text"] == content
        assert memory_dict["summary"] == summary
        assert memory_dict["message_type"] == "user"
        assert "created_at" in memory_dict
        assert "updated_at" in memory_dict