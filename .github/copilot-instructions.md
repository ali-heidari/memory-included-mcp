<!-- .github/copilot-instructions.md -->
<!-- .github/copilot-instructions.md -->
# Repo-specific Copilot Instructions (concise)

Purpose
- Minimal MCP (Mendix Connector Protocol) memory server used by the GenAI Showcase App. Small FastAPI microservice demonstrating memory tools and SSE streaming for an agent integration.

Big picture
- Single-process FastAPI service that stores and retrieves short memory notes per user. Streaming endpoint (`/stream`) exposes Server-Sent Events to emulate agent/tool streaming.

Key files (start here)
- [mcp-server/main.py](mcp-server/main.py): API handlers and Pydantic request models (`StoreRequest`, `SearchRequest`).
- [mcp-server/memory.py](mcp-server/memory.py): `MemoryStore.add(user_id, content)` and `MemoryStore.search(user_id, query)` — preservable signatures.
- [mcp-server/embeddings.py](mcp-server/embeddings.py), [mcp-server/summarization.py](mcp-server/summarization.py), [mcp-server/models.py](mcp-server/models.py): helper utilities used by the service.
- [assignment Principal Engineer AI platform/create-agent.md](assignment Principal Engineer AI platform/create-agent.md): integration notes and example agent configuration.

Run & test (quick)
- Create venv and install deps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (or `pip install fastapi uvicorn` if `requirements.txt` is absent).
- Start server: `uvicorn mcp-server.main:app --reload --host 0.0.0.0 --port 8000`.
- Smoke calls (examples): `curl http://localhost:8000/`, `curl -X POST -H 'Content-Type: application/json' -d '{"user_id":"u1","content":"note"}' http://localhost:8000/store_memory`, `curl -N http://localhost:8000/stream`.
- Tests: run `./run_tests.sh` or `pytest -q`. Check `test_mcp_server.py` for expectations.

Conventions & patterns
- Use Pydantic models for API payloads — keep shapes stable (see `StoreRequest`, `SearchRequest`).
- `MemoryStore.search` is a case-insensitive substring match and the app currently returns up to 3 hits (`results[:3]`). Tests and integrations rely on that behaviour.
- SSE streaming is implemented in `/stream` — keep event framing intact if modifying streaming logic.
- Code favors simplicity (no auth, no pagination, no ranking). When adding features, update examples and tests.

Integration notes & safe changes
- The Mendix agent calls `/store_memory` and `/search_memory`. If you add persistence, preserve `MemoryStore.add` and `MemoryStore.search` signatures for backward compatibility.
- If you change request/response shapes, update `assignment Principal Engineer AI platform/create-agent.md` and test examples.

Where to look next
- Start with [mcp-server/memory.py](mcp-server/memory.py) and [mcp-server/main.py](mcp-server/main.py), then run the server and exercise the three endpoints.
- For agent integration details see [assignment Principal Engineer AI platform/create-agent.md](assignment Principal Engineer AI platform/create-agent.md).

If you want this expanded (CI, persistent store examples, improved tests), tell me which area to prioritize.
# store memory
