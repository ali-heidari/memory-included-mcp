<!-- .github/copilot-instructions.md -->
# Repo-specific Copilot Instructions

This project implements a minimal MCP (Mendix Connector Protocol) memory server used by the GenAI Showcase App. The guidance below is focused and actionable for an AI coding assistant working in this repository.

Key files
- `mcp-server/main.py`: FastAPI app exposing MCP-like tools: `/store_memory`, `/search_memory`, `/stream`, and `/` health-check.
- `mcp-server/memory.py`: in-memory `MemoryStore` (defaultdict list) with `add(user_id, content)` and naive `search(user_id, query)` (case-insensitive substring match).
- `assignment Principal Engineer AI platform/create-agent.md`: instructions for integrating this MCP server into the Mendix GenAI Showcase App (useful for context and manual testing).
- `assignment Principal Engineer AI platform/interview-assignment.md`: assignment requirements and publishing instructions (e.g. `git bundle create assignment.bundle --all`).

Big-picture architecture and intent
- Single-process Python FastAPI microservice providing a tiny memory backend for agents. It's intentionally minimal and ephemeral (in-memory store). Persisting data or scaling is out-of-scope for current code.
- The app intentionally exposes a streaming endpoint (`/stream`) implementing Server-Sent Events (SSE) to demonstrate streaming/tool responses expected by the Mendix agent integration.
- Integration point: the Mendix GenAI Showcase App will call `/store_memory` to persist conversation notes and `/search_memory` to retrieve relevant notes for new conversations.

Developer workflows (how to run & test)
- Install dependencies (not provided). Typical Python env commands:

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn
```

- Run locally from repo root:

```bash
uvicorn mcp-server.main:app --reload --host 0.0.0.0 --port 8000
```

- Quick endpoint smoke tests:

```bash
# health
curl http://localhost:8000/

# store memory
curl -X POST -H "Content-Type: application/json" -d '{"user_id":"u1","content":"Liked Mendix AI features"}' http://localhost:8000/store_memory

# search memory
curl -X POST -H "Content-Type: application/json" -d '{"user_id":"u1","query":"Mendix"}' http://localhost:8000/search_memory

# SSE streaming demo (keep connection open)
curl -N http://localhost:8000/stream
```

Patterns and conventions specific to this repo
- Minimal synchronous handlers: endpoints use normal def/async but rely on the small `MemoryStore`. Code favors simplicity over production concerns (no auth, no paging, no ranking).
- Pydantic models are used for request payloads: `StoreRequest` and `SearchRequest` in `mcp-server/main.py` — preserve these shapes when creating client calls.
- Search is a naive substring match returning up to 3 hits (`results[:3]`). If adding retrieval logic, update both `memory.py` and any tests that assume this limit.

Integration notes & expectations
- Mendix agent will treat the server as a tool providing memory capabilities; ensure `/stream` supports SSE when testing agent streaming flows.
- The assignment expects exporting an agent definition and optionally a git bundle; see `assignment Principal Engineer AI platform/interview-assignment.md` for the exact `git bundle` command.

Safe change recommendations (what to update carefully)
- If you add persistence (Redis, SQLite), preserve the `add(user_id, content)` and `search(user_id, query)` signatures so the rest of the app can remain unchanged.
- If you change API shapes, update `create-agent.md` and test calls used by the Mendix app.

What an AI assistant should do first when contributing
- Run the server locally and exercise the three endpoints above.
- Read `mcp-server/memory.py` to understand the current retrieval behavior before modifying search logic.
- When adding features, include small smoke-test scripts or curl examples in the repo so human reviewers can validate quickly.

Files to reference in PRs and code comments
- Always point reviewers to `mcp-server/main.py` and `mcp-server/memory.py` for behavior changes.
- For commits related to agent integration, reference `assignment Principal Engineer AI platform/create-agent.md` and `assignment Principal Engineer AI platform/interview-assignment.md`.

If anything is unclear or you want me to expand sections (e.g., add a `requirements.txt`, CI steps, or a persistent store example), tell me which area to prioritize.
