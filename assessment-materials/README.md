# Mendix Agent Memory MCP Server

This project implements a minimal MCP (Mendix Connector Protocol) memory server that provides persistent memory capabilities for AI agents in the Mendix GenAI Showcase App. The server allows agents to store and retrieve conversation notes across sessions, enabling contextual awareness in user interactions.

## Architecture

The system consists of a single-process Python FastAPI microservice with SQLite persistence and semantic memory search support. Key components:

- **MCP Server** (`mcp_server/main.py`): FastAPI application exposing MCP-compatible endpoints
- **Database** (`mcp_server/database.py`): SQLite persistence for stored memories and metadata
- **Embedding Search** (`mcp_server/embeddings.py`): Vector embeddings for semantic memory retrieval
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

- **Memory Logic**: Uses SQLite persistence with semantic similarity search from embeddings
- **Storage**: SQLite-based storage for durable memory records and metadata
- **Streaming**: SSE implementation for demonstration purposes

For production use, consider adding:

- Authentication and rate limiting
- Pagination and query filtering
- Monitoring and observability
- Comprehensive testing

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
