# Architecture Context - MCP Memory Server

## System Overview

Single-process FastAPI microservice that provides persistent memory storage for Mendix AI agents.

## Layer Architecture

### 1. API Layer (`mcp_server/main.py`)
- FastAPI application with 7 main endpoints
- Request/response validation via Pydantic models
- Orchestrates database, embeddings, and summarization
- Streaming support via Server-Sent Events (SSE)

### 2. Database Layer (`mcp_server/database.py`)
- SQLAlchemy ORM abstraction
- SQLite file-based persistence (`.db` file)
- `Conversation` model with fields:
  - `id`: UUID primary key
  - `user_id`: string (indexed for fast lookups)
  - `original_text`: full content
  - `summary`: auto-generated summary
  - `vector_embedding`: binary blob (serialized numpy array)
  - `created_at`, `updated_at`: timestamps
- CRUD methods: `add_memory()`, `get_memory_by_id()`, `search_by_user()`, `delete_memory()`

### 3. Semantic Search Layer (`mcp_server/embeddings.py`)
- Lazy-loads sentence-transformers model on first use
- Converts text → 384-dimensional vectors
- Performs cosine similarity ranking
- Returns top-k results above threshold
- Model caching to avoid reloading

### 4. Processing Layer (`mcp_server/summarization.py`)
- Reduces content size before storage
- Smart fallback strategy (abstractive → extractive → truncate)
- Configurable min/max lengths
- Preserves semantic meaning for search

### 5. Configuration Layer (`mcp_server/config.py`)
- Centralized settings management
- Environment variable support
- Controls: database path, model selection, API port, summary rules

## Data Flow

```
Request
  ↓
[Pydantic Validation] (models.py)
  ↓
[Summarization] (summarization.py) - reduces text size
  ↓
[Embedding Generation] (embeddings.py) - text → vector
  ↓
[Database Store] (database.py) - SQLite persistence
  ↓
Response with metadata
```

## Search Flow

```
Query Request
  ↓
[Query Embedding] (embeddings.py) - convert to vector
  ↓
[Similarity Search] (embeddings.py) - cosine similarity ranking
  ↓
[Database Fetch] (database.py) - retrieve full records
  ↓
Response with ranked results
```

## Database Schema

```sql
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(36),
    original_text TEXT NOT NULL,
    summary TEXT,
    vector_embedding BLOB,
    message_type VARCHAR(50),
    created_at DATETIME,
    updated_at DATETIME
);

CREATE INDEX idx_user_id ON conversations(user_id);
CREATE INDEX idx_conversation_id ON conversations(conversation_id);
```

## Key Design Decisions

1. **SQLite over in-memory**: Durable storage across restarts
2. **Vector embeddings**: Enable semantic (not just keyword) search
3. **Summarization**: Reduces storage footprint while preserving meaning
4. **Single-process**: Simpler deployment, no distributed complexity
5. **Lazy model loading**: Only load embeddings model when needed
6. **Pydantic validation**: Automatic API contract enforcement

## Configuration Points

- `DB_PATH`: SQLite database file location
- `EMBEDDING_MODEL_NAME`: sentence-transformers model (default: "all-MiniLM-L6-v2")
- `VECTOR_SIMILARITY_THRESHOLD`: Minimum similarity score for results
- `SUMMARIZATION_MAX_LENGTH`: Max summary character length
- `SUMMARIZATION_MIN_LENGTH`: Min summary character length
- `API_HOST`, `API_PORT`: Server binding

## Performance Characteristics

- Embedding generation: ~50-100ms per text
- Similarity search: ~10-20ms for 100 memories
- Database query: <5ms with indexed user_id
- Memory per model: ~100MB (sentence-transformers)

## Extension Points

Future enhancements would touch:
- Database layer: add new fields, relationships
- Embeddings: swap models or use different similarity metrics
- Summarization: integrate different summarizers
- API: add new endpoints (filter, sort, export)
