# API Endpoints Context

## Health Check Endpoints

### GET /
**Purpose**: Quick health check  
**Response**:
```json
{
  "message": "MCP Memory Server is running",
  "version": "2.0",
  "status": "healthy"
}
```

### GET /health
**Purpose**: Detailed health check  
**Response**:
```json
{
  "status": "ok",
  "database": "connected",
  "embeddings": "ready"
}
```

## Memory Management Endpoints

### POST /store_memory
**Purpose**: Store a new memory with auto-summarization and embedding  
**Request**:
```json
{
  "user_id": "string",
  "content": "string"
}
```
**Response**:
```json
{
  "id": "uuid",
  "summary": "string (truncated)",
  "status": "stored"
}
```
**Process**:
1. Validates input with `StoreRequest` Pydantic model
2. Summarizes content (preserves key info, reduces size)
3. Generates vector embedding from summary
4. Stores in SQLite with metadata
5. Returns UUID for future reference

**Error Cases**:
- 400: Invalid JSON or missing fields
- 500: Summarization/embedding/database error

---

### POST /search_memory
**Purpose**: Find relevant memories using semantic similarity  
**Request**:
```json
{
  "user_id": "string",
  "query": "string",
  "limit": 5
}
```
**Response**:
```json
{
  "results": [
    {
      "id": "uuid",
      "summary": "string",
      "similarity": 0.95,
      "created_at": "2026-04-12T14:59:53.127217"
    }
  ],
  "total_found": 3
}
```
**Logic**:
1. Generates embedding for query string
2. Retrieves all user's stored embeddings from DB
3. Calculates cosine similarity for each
4. Returns top-k sorted by similarity score
5. Filters by `VECTOR_SIMILARITY_THRESHOLD`

**Fallback**: If embedding generation fails, returns all user memories

---

### GET /memories/{user_id}
**Purpose**: Retrieve all memories for a user  
**Response**:
```json
{
  "user_id": "string",
  "count": 3,
  "memories": [
    {
      "id": "uuid",
      "user_id": "string",
      "conversation_id": "uuid or null",
      "original_text": "full content",
      "summary": "truncated summary",
      "message_type": "user",
      "created_at": "2026-04-12T14:59:53.127217",
      "updated_at": "2026-04-12T14:59:53.127219"
    }
  ]
}
```

---

### DELETE /memories/{memory_id}
**Purpose**: Remove a specific memory  
**Response**:
```json
{
  "status": "deleted",
  "id": "uuid"
}
```
**Error Cases**:
- 404: Memory ID not found

---

## Streaming Endpoint

### GET /stream
**Purpose**: Server-Sent Events demonstration for agent integration  
**Response** (text/event-stream):
```
data: Memory chunk 0 processed

data: Memory chunk 1 processed

data: Memory chunk 2 processed
```
**Use**: Shows streaming capability for chunked processing

---

## Legacy Compatibility Endpoint

### POST /store_memory_legacy
**Purpose**: Backward compatibility with V1 API  
**Request**: Same as `/store_memory`  
**Response**: Same as `/store_memory`  
**Note**: Maintained for compatibility; use `/store_memory` for new code

---

## Pydantic Models (Request/Response Contracts)

### StoreRequest
```python
class StoreRequest(BaseModel):
    user_id: str
    content: str
```

### StoreResponse
```python
class StoreResponse(BaseModel):
    id: str
    summary: str
    status: str = "stored"
```

### SearchRequest
```python
class SearchRequest(BaseModel):
    user_id: str
    query: str
    limit: int = 5
```

### SearchResponse
```python
class SearchResponse(BaseModel):
    results: List[MemoryResult]
    total_found: int

class MemoryResult(BaseModel):
    id: str
    summary: str
    similarity: float
    created_at: datetime
```

### ListMemoriesResponse
```python
class ListMemoriesResponse(BaseModel):
    user_id: str
    count: int
    memories: List[MemoryDetail]

class MemoryDetail(BaseModel):
    id: str
    user_id: str
    conversation_id: Optional[str]
    original_text: str
    summary: str
    message_type: str
    created_at: datetime
    updated_at: datetime
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success - operation completed |
| 400 | Bad Request - invalid JSON or missing fields |
| 404 | Not Found - memory ID does not exist |
| 500 | Internal Error - summarization, embedding, or DB failure |

---

## API Design Principles

1. **Idempotent reads**: GET endpoints always return same data for same input
2. **User isolation**: All endpoints accept `user_id` for data separation
3. **Timestamp metadata**: All stored records include creation/update time
4. **Semantic search**: Search uses vector similarity, not keyword matching
5. **Graceful degradation**: Search falls back to all records if embedding fails
