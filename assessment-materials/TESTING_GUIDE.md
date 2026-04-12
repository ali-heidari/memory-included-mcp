# MCP Server Testing Guide (Without Mendix Studio)

This guide provides multiple ways to test your MCP Memory Server without installing Mendix Studio.

## Quick Start

1. **Start the server:**
   ```bash
   cd mcp-server
   python3 main.py
   ```
   Server will run on http://localhost:8000

2. **Run automated tests:**
   ```bash
   # From project root
   python3 simple_test.py
   ```

## Testing Methods

### Method 1: Automated Python Test Script

The `simple_test.py` script tests all endpoints automatically:

```bash
python3 simple_test.py
```

This will test:
- Health checks
- Memory storage
- Memory search
- Error handling

### Method 2: Manual curl Commands

Test individual endpoints with curl:

```bash
# Health check
curl http://localhost:8000/

# List memories for a user
curl http://localhost:8000/memories/test_user

# Store a memory
curl -X POST http://localhost:8000/store_memory \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","content":"I prefer dark mode for coding"}'

# Search memories
curl -X POST http://localhost:8000/search_memory \
  -H "Content-Type: application/json" \
  -d '{"user_id":"alice","query":"dark mode"}'

# Get specific memory
curl http://localhost:8000/memories/alice/memory_123

# Test streaming (Server-Sent Events)
curl -N http://localhost:8000/stream
```

### Method 3: FastAPI Interactive Documentation

1. Start the server
2. Open http://localhost:8000/docs in your browser
3. Use the interactive Swagger UI to test endpoints
4. Click "Try it out" on any endpoint

### Method 4: Postman/Insomnia

1. Import the API collection or create requests manually:
   - Method: GET, URL: http://localhost:8000/
   - Method: POST, URL: http://localhost:8000/store_memory
     Body: `{"user_id":"test","content":"Sample memory"}`

### Method 5: Python Requests Script

```python
import requests

# Test health
response = requests.get("http://localhost:8000/")
print(response.json())

# Store memory
data = {"user_id": "test", "content": "Hello world"}
response = requests.post("http://localhost:8000/store_memory", json=data)
print(response.json())

# Search memory
search = {"user_id": "test", "query": "world"}
response = requests.post("http://localhost:8000/search_memory", json=search)
print(response.json())
```

## Expected Behavior

### Successful Tests:
- Health endpoint returns: `{"message": "MCP Memory Server is running"}`
- Store memory returns: Memory ID and summary
- Search returns: List of relevant memories with similarity scores

### If ML Features Fail:
The server will still work for basic CRUD operations. Advanced features like semantic search may return basic substring matches or error messages.

## Troubleshooting

### Server Won't Start:
```bash
# Check for import errors
cd mcp-server
python3 -c "import main"

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"
```

### Connection Refused:
- Make sure server is running on port 8000
- Check if port is already in use: `lsof -i :8000`

### API Errors:
- Check request format (JSON headers)
- Verify user_id and content fields
- Look at server logs for detailed error messages

## Advanced Testing

### Load Testing:
```bash
# Install hey for load testing
# Then run:
hey -n 100 -c 10 http://localhost:8000/
```

### Database Inspection:
```bash
# Check SQLite database
sqlite3 mcp-server/memories.db
.schema
SELECT * FROM conversations LIMIT 5;
```

### Memory Usage:
Monitor the server while testing to ensure it handles memory efficiently with vector embeddings.

## Integration Test Example

Here's a complete test scenario:

1. Store multiple memories
2. Search for related content
3. Verify summaries are generated
4. Check vector similarity works

```bash
# Store memories
curl -X POST http://localhost:8000/store_memory \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","content":"Python is great for web development"}'

curl -X POST http://localhost:8000/store_memory \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","content":"FastAPI is a modern web framework for Python"}'

# Search
curl -X POST http://localhost:8000/search_memory \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","query":"web framework"}'
```

This should return both memories with similarity scores.