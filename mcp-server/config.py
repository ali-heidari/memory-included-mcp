# Configuration for MCP Server

import os
from pathlib import Path

# Database configuration
DB_PATH = os.getenv("DB_PATH", "memory.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Embedding model configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Summarization configuration
SUMMARIZATION_MAX_LENGTH = int(os.getenv("SUMMARIZATION_MAX_LENGTH", "150"))
SUMMARIZATION_MIN_LENGTH = int(os.getenv("SUMMARIZATION_MIN_LENGTH", "30"))

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Vector search configuration
VECTOR_SIMILARITY_THRESHOLD = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.3"))
SEARCH_RESULTS_LIMIT = int(os.getenv("SEARCH_RESULTS_LIMIT", "5"))

# Summary length rules
SUMMARY_RULES = {
    "short": {"max_chars": 100, "summary_length": 30},
    "medium": {"max_chars": 500, "summary_length": 50},
    "long": {"max_chars": float("inf"), "summary_length": 150},
}
