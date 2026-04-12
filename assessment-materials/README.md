# Mendix Agent Memory MCP Server

This repository contains the Mendix MCP Memory Server implementation for the AI Platform interview assignment.

The interviewer specifically asked to see the thought process, architecture, and file responsibilities. This README is written with that goal in mind.

## What this project is trying to solve

The core problem is: AI agents need memory.

A Mendix-compatible MCP server should be able to:

- store conversation memory reliably
- summarize and persist important content
- retrieve relevant memories later
- expose simple, testable HTTP APIs
- support a streaming integration path

## My thought process

### 1. Understand the assignment

The assignment asked for an MCP memory server, not a research prototype. That means prioritizing:

- clarity over cleverness
- predictable behavior over experimental features
- documented design over hidden implementation details

### 2. Choose tools that make the design visible

I selected:

- Python + FastAPI for readable REST API and automatic validation
- SQLite for storage so persistence is concrete and reproducible
- Pydantic models to explicitly define API contracts

These choices make the project easy to inspect and understand.

### 3. Structure based on single responsibility

Each module focuses on one thing:

- main application and routing
- database schema and persistence
- embeddings and semantic search
- summarization
- configuration

That keeps the implementation maintainable and reviewable.

### 4. Validate with real API tests

I verified the service with manual curl commands for every endpoint.

The results are recorded in this document so the interviewer can see both the design and the actual behavior.

## Project structure

### `mcp_server/main.py`

This is the entry point for the service.

- defines the FastAPI app and all endpoints
- orchestrates summarization, embedding creation, and database writes
- includes health checks, search, list, delete, streaming, and legacy compatibility

### `mcp_server/database.py`

This file defines the data model and persistence layer.

- SQLAlchemy ORM model for conversations
- SQLite engine and session factory
- CRUD methods for storing, retrieving, searching, and deleting memories

### `mcp_server/models.py`

This file defines Pydantic models used by the API.

- request shapes: `StoreRequest`, `SearchRequest`
- response shapes: `StoreResponse`, `SearchResponse`, `ListMemoriesResponse`
- typed results: `MemoryResult`, `MemoryDetail`

Using Pydantic means the API is self-validating and easy to document.

### `mcp_server/embeddings.py`

This file contains semantic search utilities.

- loads the sentence-transformers model lazily
- converts text into embeddings
- performs cosine similarity ranking

This component is a clean abstraction so the search logic is separated from the API and storage logic.

### `mcp_server/summarization.py`

This file contains the summarization logic that runs before storage.

- reduces content size
- preserves meaning for search and display
- applies configured min/max summary lengths

Summaries help keep stored memory concise and searchable.

### `mcp_server/config.py`

Centralizes configuration values and environment overrides.

- database path
- embedding model selection
- API host/port
- summarization limits

This keeps deployment settings separate from code logic.

## How to run the service

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m mcp_server.main
```

Or with Uvicorn for development:

```bash
uvicorn mcp_server.main:app --reload --host 0.0.0.0 --port 8000
```

## API endpoints and usage

### Health

- `GET /`
- `GET /health`

### Store memory

- `POST /store_memory`
  - Body: `{"user_id": "string", "content": "string"}`

### Search memory

- `POST /search_memory`
  - Body: `{"user_id": "string", "query": "string", "limit": 5}`

### List memories

- `GET /memories/{user_id}`

### Delete memory

- `DELETE /memories/{memory_id}`

### Streaming

- `GET /stream`

### Legacy compatibility

- `POST /store_memory_legacy`

## Why these endpoints?

I kept the API surface small to make the design easy to evaluate:

- health endpoints prove the service is running
- store/search/list/delete cover the main memory lifecycle
- streaming shows that the service can emit chunked responses
- legacy route demonstrates compatibility with older clients

## What to read next

This README is the high-level guide. For deeper thought process and implementation details, these files are the best next step:

- [README-PROCEDURE.md](README-PROCEDURE.md) — step-by-step design and decision log
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) — technical deep dive into code and architecture
- [TESTING_GUIDE.md](TESTING_GUIDE.md) — validation strategy and test commands
- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) — summary of delivery and features

## Assessment Materials Index

- [ASSESSMENT-OVERVIEW.md](ASSESSMENT-OVERVIEW.md) — overview of this folder and how to use it
- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) — delivery summary and feature list
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) — architecture and implementation details
- [README-PROCEDURE.md](README-PROCEDURE.md) — detailed thought process
- [TESTING_GUIDE.md](TESTING_GUIDE.md) — testing instructions and evidence
- [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) — progress notes and incremental decisions
- [copilot-instructions.md](copilot-instructions.md) — repo-specific assistant guidance
- [create-agent.md](create-agent.md) — Mendix agent integration reference
- [interview-assignment.md](interview-assignment.md) — original assignment prompt

## Manual API Test Results

### Server startup

- Command used:
  - `uvicorn mcp_server.main:app --reload --host 0.0.0.0 --port 8000`
  - or equivalently: `python3 -m mcp_server.main`

### Health checks

- `curl http://localhost:8000/`
  - Response: `{"message":"MCP Memory Server is running","version":"2.0","status":"healthy"}`

- `curl http://localhost:8000/health`
  - Response: `{"status":"ok","database":"connected","embeddings":"ready"}`

### Store memory

- `curl -X POST -H 'Content-Type: application/json' -d '{"user_id": "test_user_1", "content": "This is a test conversation about machine learning and AI development. We discussed neural networks, deep learning algorithms, and the future of artificial intelligence in enterprise applications."}' http://localhost:8000/store_memory`
  - Result: `{"id":"e322f277-abff-4e7c-84db-181162acb7ba","summary":"This is a test conversation about machine...","status":"stored"}`

- `curl -X POST -H 'Content-Type: application/json' -d '{"user_id": "test_user_1", "content": "Today we worked on database optimization techniques. We implemented indexing strategies, query optimization, and explored different database architectures for high-performance applications."}' http://localhost:8000/store_memory`
  - Result: `{"id":"12a9ad62-af88-4a99-990f-439a95b0aa15","summary":"Today we worked on database optimization...","status":"stored"}`

### Search memory

- `curl -X POST -H 'Content-Type: application/json' -d '{"user_id": "test_user_1", "query": "machine learning algorithms", "limit": 5}' http://localhost:8000/search_memory`
  - Result: returned 3 memories with similarity scores and timestamps

### List memories

- `curl http://localhost:8000/memories/test_user_1`
  - Result: returned 3 stored memories for `test_user_1`, including full original text, summaries, and metadata

### Streaming endpoint

- `curl -N http://localhost:8000/stream`
  - Result: streamed SSE messages:
    - `data: Memory chunk 0 processed`
    - `data: Memory chunk 1 processed`
    - `data: Memory chunk 2 processed`
    - `data: Memory chunk 3 processed`
    - `data: Memory chunk 4 processed`

### Legacy compatibility endpoint

- `curl -X POST -H 'Content-Type: application/json' -d '{"user_id": "test_user_2", "content": "Legacy API test: This is an older format for storing memories in the system."}' http://localhost:8000/store_memory_legacy`
  - Result: `{"id":"479d7ed9-4c9c-40cb-9d3d-8dbc9b2c4c7a","summary":"Legacy API test: This is an older format for storing memories in the system.","status":"stored"}`

### Delete memory

- Example delete command:
  - `curl -X DELETE http://localhost:8000/memories/{memory_id}`

- Note: in the provided test the placeholder `memory_id_here` returned a 404 because it was not replaced with a real memory ID. Use one of the stored IDs above to delete a real memory.

## Files

- `mcp_server/main.py` - FastAPI application with MCP endpoints
- `mcp_server/memory.py` - Memory storage and search logic
- `assignment Principal Engineer AI platform/` - Assignment documentation and integration guides
- `.github/copilot-instructions.md` - AI assistant guidance for this codebase
