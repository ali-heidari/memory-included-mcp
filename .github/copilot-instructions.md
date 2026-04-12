<!-- .github/copilot-instructions.md -->
# Copilot Instructions - Quick Reference & Navigation

**Purpose**: MCP (Mendix Connector Protocol) memory server for GenAI agents  
**Type**: FastAPI microservice with SQLite persistence and semantic search

## ⚡ Quick Start (5 mins)

```bash
# Install & run
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m mcp_server.main

# Test endpoint
curl http://localhost:8000/
curl -X POST -H 'Content-Type: application/json' \
  -d '{"user_id":"test","content":"Hello world"}' \
  http://localhost:8000/store_memory
```

## 📚 Modular Documentation Index

Use these files for specific tasks:

### **System Understanding**
- [architecture.md](ai-context/architecture.md) — System design, layers, data flow, schema

### **API Development**
- [api-endpoints.md](ai-context/api-endpoints.md) — All endpoints, request/response formats, status codes

### **Code Standards**
- [coding-standards.md](ai-context/coding-standards.md) — Patterns, validation, error handling, testing

### **Feature Deep-Dives**
- [features/embeddings.md](ai-context/features/embeddings.md) — Vector embeddings, semantic search, similarity ranking
- [features/summarization.md](ai-context/features/summarization.md) — Text summarization, storage reduction, fallback strategy

## 🎯 Quick Navigation by Task

| Task | Read These Files (in order) |
|------|---------------------------|
| **Add new API endpoint** | architecture.md → api-endpoints.md → coding-standards.md |
| **Fix embedding bug** | features/embeddings.md → coding-standards.md |
| **Modify summarization** | features/summarization.md → architecture.md |
| **Database changes** | architecture.md → coding-standards.md |
| **New feature** | architecture.md → relevant feature file → api-endpoints.md |
| **Code review** | coding-standards.md → relevant feature file |
| **Deployment issue** | architecture.md + config context in main.py |

## 🗂️ Key Files

- `mcp_server/main.py` — FastAPI app with 7 endpoints
- `mcp_server/database.py` — SQLAlchemy ORM + CRUD
- `mcp_server/models.py` — Pydantic request/response models
- `mcp_server/embeddings.py` — Vector embeddings & similarity search
- `mcp_server/summarization.py` — Text summarization
- `mcp_server/config.py` — Configuration & env variables

## 🏗️ Architecture at a Glance

```
Request → Validation (Pydantic)
        → Summarization (text reduction)
        → Embedding (vector generation)
        → Database (SQLite store)
        → Response (JSON metadata)
```

## 📋 Key Conventions

- Use **Pydantic models** for all API inputs/outputs
- Store **embeddings as BLOB** in database
- Summarize **before** embedding
- Always **include user_id** for data isolation
- **Graceful degradation** on embedding failure

## ⚙️ Configuration

Set via environment variables or `.github/ai-context/` files:

```python
DB_PATH = "memory.db"                              # Database file
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"          # Sentence transformer
VECTOR_SIMILARITY_THRESHOLD = 0.7                  # Search threshold
SUMMARIZATION_MAX_LENGTH = 150                     # Summary max chars
API_PORT = 8000                                    # Server port
```

## 🧪 Testing

```bash
./run_tests.sh              # All tests
pytest tests/test_api.py    # API tests only
pytest -v                   # Verbose output
```

## 🚀 Common Tasks

**Add API endpoint?** → See [api-endpoints.md](ai-context/api-endpoints.md) for pattern + [coding-standards.md](ai-context/coding-standards.md) for Pydantic model structure

**Improve search?** → See [features/embeddings.md](ai-context/features/embeddings.md) for similarity logic + threshold tuning

**Database schema change?** → See [architecture.md](ai-context/architecture.md) for schema + [coding-standards.md](ai-context/coding-standards.md) for SQLAlchemy patterns

**Summarization issue?** → See [features/summarization.md](ai-context/features/summarization.md) for fallback chain

## � After Adding a Feature

**Always update docs to keep them in sync with code:**

1. ✅ **api-endpoints.md** — Add endpoint with request/response examples + status codes
2. ✅ **architecture.md** — Update if data flow or schema changed
3. ✅ **coding-standards.md** — Add pattern example if you introduced a new pattern
4. ✅ **features/[feature].md** — Create or update feature-specific deep-dive
5. ✅ **models.py docstring** — Document new Pydantic models
6. ✅ **Run tests** — `pytest tests/` to validate changes
7. ✅ **Commit message** — Follow format: `[feature|fix|refactor]: description + affected docs`

**Example workflow (add new endpoint)**:
```
1. Add endpoint to main.py
2. Add Pydantic model to models.py
3. Update api-endpoints.md with new endpoint section
4. Update architecture.md if data flow changed
5. Add tests in tests/test_api.py
6. Run: pytest tests/
7. Commit: [feature]: Add /new_endpoint - updated api-endpoints.md, models.py
```

**Why?** Next agent task receives fresh context = fewer debugging loops

## �💡 Pro Tips

1. **First call slow?** Embedding model loads on first /store_memory → cached after
2. **No search results?** Check VECTOR_SIMILARITY_THRESHOLD in config
3. **Database locked?** SQLite limitation → use file-based mutex or upgrade to PostgreSQL
4. **Memory usage?** Models (~100MB) + embeddings (1.5KB each) → plan storage

## 📞 When Stuck

1. Check relevant documentation file above
2. Look at existing endpoint implementation in `main.py`
3. Review tests in `tests/` for working examples
4. Check error logs with `logger.error()` context

---

**Last Updated**: April 2026  
**For detailed thought process & human-readable guide**: See `assessment-materials/README.md`
