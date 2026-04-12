# Mendix Agent Memory MCP Server

This project implements a minimal MCP (Mendix Connector Protocol) memory server that provides persistent memory capabilities for AI agents in the Mendix GenAI Showcase App. The server allows agents to store and retrieve conversation notes across sessions, enabling contextual awareness in user interactions.

## Architecture

The system consists of a single-process Python FastAPI microservice with an in-memory memory store (intentionally minimal for the assignment). Key components:

- **MCP Server** (`mcp_server/main.py`): FastAPI application exposing MCP-compatible endpoints
- **Memory Store** (`mcp_server/memory.py`): Simple in-memory storage with naive substring search
- **Integration**: Connects to Mendix GenAI Showcase App via HTTP APIs

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation & Run

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn

# Run the server
uvicorn mcp_server.main:app --reload --host 0.0.0.0 --port 8000
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/

# Store memory
curl -X POST -H "Content-Type: application/json" \
  -d '{"user_id":"user123","content":"User prefers dark mode interface"}' \
  http://localhost:8000/store_memory

# Search memory
curl -X POST -H "Content-Type: application/json" \
  -d '{"user_id":"user123","query":"dark"}' \
  http://localhost:8000/search_memory

# Test streaming (SSE)
curl -N http://localhost:8000/stream
```

## API Endpoints

- `GET /` - Health check
- `POST /store_memory` - Store conversation notes
  - Body: `{"user_id": "string", "content": "string"}`
- `POST /search_memory` - Retrieve relevant memories
  - Body: `{"user_id": "string", "query": "string"}`
  - Returns: `{"results": ["memory1", "memory2", ...]}`
- `GET /stream` - Server-Sent Events streaming demo

## Integration with Mendix

This MCP server is designed to integrate with the Mendix GenAI Showcase App:

1. Configure the MCP server endpoint in the Mendix app
2. Create an agent using the Agent Builder
3. Add this MCP server as a tool to the agent
4. The agent can now store/retrieve memories during conversations

## Assignment Context

This implementation fulfills the Principal Engineer AI Platform interview assignment requirements:

- MCP server with HTTP streaming support
- Memory persistence across conversations
- Integration with Mendix GenAI Showcase App
- Export via `git bundle create assignment.bundle --all`

## Development

- **Memory Logic**: Currently uses naive substring matching, returns top 3 results
- **Storage**: In-memory only (ephemeral) - intentionally minimal for assignment
- **Streaming**: SSE implementation for demonstration purposes

For production use, consider adding:

- Persistent storage (SQLite, Redis)
- Vector embeddings for semantic search
- Authentication and rate limiting
- Comprehensive testing

## Files

- `mcp_server/main.py` - FastAPI application with MCP endpoints
- `mcp_server/memory.py` - Memory storage and search logic
- `assignment Principal Engineer AI platform/` - Assignment documentation and integration guides
- `.github/copilot-instructions.md` - AI assistant guidance for this codebase
