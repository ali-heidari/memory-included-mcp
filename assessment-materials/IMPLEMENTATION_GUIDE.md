# Implementation Guide - MCP Server V2

## Architecture Overview

This document explains the complete implementation of the Mendix MCP Memory Server V2 with persistent storage, semantic search, and auto-summarization.

---

## Key Components

### 1. Configuration (`config.py`)

Centralized configuration management with environment variable support.

**Key settings:**
- `DB_URL`: SQLite database path
- `EMBEDDING_MODEL_NAME`: sentence-transformers model
- `VECTOR_SIMILARITY_THRESHOLD`: Minimum similarity score for search results
- `SUMMARY_RULES`: Length-based summarization configuration

**Usage:**
```python
from config import DB_PATH, API_PORT
```

### 2. Data Models (`models.py`)

Pydantic models for request/response validation and type safety.

**Key models:**
- `StoreRequest`: Input for storing memory (user_id, content)
- `StoreResponse`: Output after storing (id, summary, status)
- `SearchRequest`: Input for search (user_id, query, limit)
- `SearchResponse`: Output with ranked results
- `MemoryResult`: Single result item with similarity score
- `MemoryDetail`: Full memory with all metadata

**Benefits:**
- ✅ Automatic validation
- ✅ Auto-generated OpenAPI/Swagger docs
- ✅ Type hints for IDE support
- ✅ JSON serialization

### 3. Database Layer (`database.py`)

SQLAlchemy ORM providing abstraction and CRUD operations.

**Schema:**
```
conversations table
├── id (TEXT, PRIMARY KEY, UUID)
├── user_id (TEXT, indexed)
├── conversation_id (TEXT, for grouping)
├── original_text (TEXT, full message)
├── summary (TEXT, compact version)
├── vector_embedding (BLOB, serialized numpy array)
├── message_type (TEXT, 'user'|'agent')
├── created_at (DATETIME)
├── updated_at (DATETIME)
└── Composite index: (user_id, created_at)
```

**CRUD Operations:**
```python
db.add_memory(user_id, original_text, summary, vector_embedding)
db.search_by_user(user_id, limit=10)
db.get_memory_by_id(memory_id)
db.delete_memory(memory_id)
db.get_all_embeddings(user_id)
```

**Why ORM?**
- Prevents SQL injection
- Database-agnostic (easy migration to PostgreSQL)
- Relationship management
- Migration support (via Alembic)

### 4. Embeddings (`embeddings.py`)

Vector generation and semantic similarity search.

**Flow:**
```
Text → SentenceTransformer → 384-dim vector → Pickle → BLOB storage
Query → SentenceTransformer → 384-dim vector → Cosine similarity → Ranked results
```

**Key functions:**
- `generate_embedding(text)`: Convert text to vector, serialize to bytes
- `deserialize_embedding(bytes)`: Load vector from storage
- `cosine_similarity(vec1, vec2)`: Calculate similarity (0-1 range)
- `search_similar_embeddings()`: Find top-k similar memories

**Why sentence-transformers?**
- Pre-trained on semantic similarity tasks
- 384-dimensional vectors (small model: ~50MB)
- Fast inference (~10ms per sentence)
- Works for domain-specific text

**Example:**
```
Query: "What does user prefer?"
Memory 1: "User likes dark mode" → similarity: 0.72 ✅
Memory 2: "App is blue" → similarity: 0.31 ❌
```

### 5. Summarization (`summarization.py`)

Intelligent text condensation with fallback strategies.

**Strategy:**
```
1. Text < 100 chars → Return as-is
2. Try abstractive (transformer model) → Generates new text
3. Fallback to extractive → Select important sentences
4. Last resort → Truncate with ellipsis
```

**Configuration by length:**
```python
SUMMARY_RULES = {
    "short": {"max_chars": 100, "summary_length": 30},
    "medium": {"max_chars": 500, "summary_length": 50},
    "long": {"max_chars": inf, "summary_length": 150},
}
```

**Why?**
- Stores 70-90% less data
- Improves search relevance (less noise)
- Readable in UI
- Preserves key information

**Example:**
```
Original (120 chars):
"So like, uh, hello! How are you doing? Anyway, I wanted to ask 
about dark mode because I really really love it and think it's best."

Summarized (25 chars):
"User likes dark mode"
```

### 6. Main API (`main.py`)

FastAPI application exposing all endpoints with integrated workflows.

**Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health check |
| GET | `/health` | Detailed health |
| POST | `/store_memory` | Store + summarize + embed |
| POST | `/search_memory` | Semantic search |
| GET | `/memories/{user_id}` | List all user memories |
| DELETE | `/memories/{id}` | Delete memory |
| GET | `/stream` | SSE streaming demo |

**Flow for `/store_memory`:**
```
1. User sends: {"user_id": "u1", "content": "User loves dark mode"}
2. Server summarizes → "User loves dark mode"
3. Server generates embedding → [0.2, -0.5, 0.8, ...]
4. Server stores in SQLite with all metadata
5. Returns: {"id": "mem_abc123", "summary": "...", "status": "stored"}
```

**Flow for `/search_memory`:**
```
1. User sends: {"user_id": "u1", "query": "What does user like?"}
2. Server generates query embedding
3. Server retrieves all user's embeddings from DB
4. Server calculates cosine similarity for each
5. Server ranks by similarity
6. Returns top-5 with scores:
   [
     {"id": "mem_abc", "summary": "User loves dark mode", "similarity": 0.87},
     {"id": "mem_def", "summary": "User prefers keyboard", "similarity": 0.71}
   ]
```

---

## Data Flow Diagram

```
┌─────────────┐
│   Mendix    │
│   Agent     │
└──────┬──────┘
       │
       ├─→ POST /store_memory
       │   {"user_id": "u1", "content": "..."}
       │
       ├─→ main.py:store_memory()
       │   ├─→ summarization.summarize()
       │   ├─→ embeddings.generate_embedding()
       │   └─→ database.add_memory()
       │       └─→ SQLite:conversations
       │
       ├─→ POST /search_memory
       │   {"user_id": "u1", "query": "..."}
       │
       ├─→ main.py:search_memory()
       │   ├─→ embeddings.generate_embedding()
       │   ├─→ database.get_all_embeddings()
       │   ├─→ embeddings.search_similar_embeddings()
       │   └─→ database.get_memory_by_id()
       │
       └─→ Response with ranked memories
```

---

## Running the Server

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# From repo root
cd mcp_server
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Test

```bash
# Health check
curl http://localhost:8000/health

# Store memory
curl -X POST http://localhost:8000/store_memory \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user1","content":"I like dark mode and keyboard shortcuts"}'

# Search memory
curl -X POST http://localhost:8000/search_memory \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user1","query":"preferences","limit":5}'

# List all memories
curl http://localhost:8000/memories/user1

# Delete memory
curl -X DELETE http://localhost:8000/memories/mem_abc123
```

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Embedding generation | ~10-15ms | First load: 500ms (model init) |
| Summarization | ~200-300ms | Depends on text length |
| Store memory | ~300-400ms | Embedding + summarize + DB write |
| Search memory | ~50-100ms | Similarity search + DB lookup |
| Database query | ~5-10ms | With indexes |

---

## Design Decisions Explained

### 1. Why Lazy-Load Models?

**Decision:** Load embedding/summarization models on first use

```python
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model
```

**Why?**
- Server starts in <1 second (not 5-10 seconds)
- Saves memory if endpoints aren't used
- Better experience for quick health checks

### 2. Why Serialize Embeddings?

**Decision:** Store vectors as pickle bytes in SQLite BLOB

**Alternatives:**
- Store in separate vector DB (overkill for MVP)
- Store as JSON (larger, slower)
- Store as pickle (chosen)

**Why pickle?**
- Preserves numpy dtype information
- Fast serialization (~1ms)
- Built-in Python library
- Good enough for single-server

### 3. Why Dual Text Storage?

**Decision:** Store both `original_text` and `summary`

**Why?**
- `original_text`: Audit trail, detailed context
- `summary`: Compact, searchable, displayable
- Allows future improvements (re-summarize with better model)

### 4. Why ORM Instead of Raw SQL?

**Decision:** Use SQLAlchemy ORM

**Trade-off:**
- ✅ Database-agnostic
- ✅ Prevents SQL injection
- ✅ Type safe
- ✅ Easy migrations
- ❌ ~10% performance overhead (negligible)

**When not to use ORM:** High-throughput (>10k req/s) analytical queries

---

## Future Improvements

### V3 Roadmap

1. **Vector Database**
   - Use ChromaDB or FAISS for 1M+ memories
   - Fast similarity search with LSH hashing

2. **Conversation Clustering**
   - Group related memories automatically
   - Reduce redundancy

3. **Caching Layer**
   - Redis for frequently accessed memories
   - TTL: 1 hour

4. **Analytics**
   - Track popular topics
   - User behavior insights

5. **Multi-language**
   - Support multilingual embeddings
   - Auto-detect + translate

---

## Troubleshooting

**Issue:** "sentence-transformers not installed"
**Solution:** `pip install sentence-transformers`

**Issue:** "transformers not installed"
**Solution:** `pip install transformers`

**Issue:** Very slow first request
**Solution:** Models lazy-load on first use (~500ms). Subsequent requests are 10-20ms.

**Issue:** Memory usage growing
**Solution:** Implement TTL cleanup. See future roadmap.

---

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_api.py::test_store_memory

# With coverage
pytest --cov=mcp_server tests/
```

---

## API Documentation

Automatic OpenAPI docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## References

- [SQLAlchemy ORM](https://www.sqlalchemy.org)
- [Sentence-Transformers](https://www.sbert.net)
- [FastAPI](https://fastapi.tiangolo.com)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)
