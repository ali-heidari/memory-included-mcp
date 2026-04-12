# Embeddings Feature Context

## Feature Overview

Embeddings enable semantic search by converting text into vector representations, allowing similarity-based matching rather than keyword-only search.

## Location
- **Main code**: `mcp_server/embeddings.py`
- **Called from**: `mcp_server/main.py` (store_memory and search_memory endpoints)
- **Configuration**: `mcp_server/config.py` (model name, threshold)

## How It Works

### 1. Vector Generation (`generate_embedding`)

```python
def generate_embedding(text: str) -> bytes
```

**Process**:
1. Load sentence-transformers model (lazy, cached)
2. Convert text string → 384-dimensional vector (numpy array)
3. Serialize vector to bytes (for storage in SQLite BLOB)
4. Return bytes

**Input**: Any text string (can be original text or summary)  
**Output**: Binary blob for database storage

**Performance**: ~50-100ms per call (first call loads model ~500ms)

### 2. Similarity Ranking (`search_similar_embeddings`)

```python
def search_similar_embeddings(
    query_embedding: bytes,
    stored_embeddings: List[Tuple[str, bytes]],
    top_k: int = 5,
    threshold: float = 0.7
) -> List[Tuple[str, float]]
```

**Process**:
1. Deserialize query embedding from bytes → numpy array
2. For each stored embedding:
   - Deserialize to numpy array
   - Calculate cosine similarity with query
   - If similarity > threshold, keep result
3. Sort by similarity (descending)
4. Return top-k results

**Cosine Similarity**: Ranges 0.0 (opposite) to 1.0 (identical)  
**Typical results**: Semantic matches are 0.7-0.95+

**Example**:
```
Query: "machine learning algorithms"
Result 1: "deep learning and neural networks" (similarity: 0.92)
Result 2: "python programming basics" (similarity: 0.45 - filtered out)
Result 3: "AI development techniques" (similarity: 0.88)
```

### 3. Model Management (`get_embedding_model`)

```python
def get_embedding_model() -> SentenceTransformer
```

**Strategy**: Lazy loading and caching
- First call: Downloads and caches model (~100MB to disk)
- Subsequent calls: Returns cached model
- Avoids startup delays, saves memory on unused features

**Model**: `all-MiniLM-L6-v2` (default)
- Lightweight: ~33M parameters
- Fast: ~50ms per embedding
- Dimension: 384 (good balance of speed/quality)
- Trained on semantic similarity tasks

## Integration Points

### In `/store_memory` Endpoint

```python
# Step 1: Summarize content
summary = summarize(req.content)

# Step 2: Generate embedding (this module)
embedding_bytes = generate_embedding(summary)

# Step 3: Store with embedding
memory = db.add_memory(
    user_id=req.user_id,
    summary=summary,
    vector_embedding=embedding_bytes  # Stored as BLOB
)
```

### In `/search_memory` Endpoint

```python
# Step 1: Generate query embedding
query_embedding = generate_embedding(req.query)

# Step 2: Get all user's stored embeddings from DB
stored_embeddings = db.get_all_embeddings(req.user_id)

# Step 3: Find similar ones (this module)
similar = search_similar_embeddings(
    query_embedding,
    stored_embeddings,
    top_k=req.limit,
    threshold=VECTOR_SIMILARITY_THRESHOLD
)

# Step 4: Fetch full records and return
results = [db.get_memory_by_id(memory_id) for memory_id, score in similar]
```

## Configuration

Set these in `config.py` or environment variables:

```python
# Model selection
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Default lightweight model
# Alternatives: "all-MiniLM-L12-v2" (faster), "all-mpnet-base-v2" (better quality)

# Search filtering
VECTOR_SIMILARITY_THRESHOLD = 0.7  # Only return results above this score
# Typical range: 0.6-0.8 depending on desired recall vs precision
```

## Database Storage

Embeddings stored as BLOB (binary) in the `conversations` table:

```sql
CREATE TABLE conversations (
    -- ... other fields ...
    vector_embedding BLOB,  -- Serialized numpy array
    -- ... other fields ...
);
```

**Serialization**:
- numpy array → bytes via `np.asarray(array).tobytes()`
- bytes → numpy array via `np.frombuffer(bytes).reshape(384)`
- Size: 384 × 4 bytes = ~1.5KB per embedding

## Fallback Strategy

If embedding generation fails:

```python
if query_embedding is None:
    logger.warning("Could not generate query embedding - falling back")
    # Return all user's memories instead of ranked search
    memories = db.search_by_user(req.user_id, limit=req.limit)
    return SearchResponse(results=memories, total_found=len(memories))
```

This ensures search still works even if model fails to load.

## Performance Characteristics

| Operation | Time |
|-----------|------|
| Generate embedding (warm) | 50-100ms |
| Generate embedding (cold, load model) | 500-1000ms |
| Cosine similarity per record | <1ms |
| Total search with 100 memories | ~20-30ms |
| Memory footprint (model) | ~100MB |

## Common Modifications

### Swap Embedding Model
```python
# In config.py
EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"  # Higher quality, slower
# or
EMBEDDING_MODEL_NAME = "all-MiniLM-L12-v2"  # Faster version
```

### Adjust Similarity Threshold
```python
# In config.py
VECTOR_SIMILARITY_THRESHOLD = 0.6  # More permissive (recall-focused)
# or
VECTOR_SIMILARITY_THRESHOLD = 0.85  # Stricter (precision-focused)
```

### Change Similarity Metric
```python
# In embeddings.py, modify search_similar_embeddings()
# Could use Euclidean distance, Manhattan distance, etc. instead of cosine
```

## Testing Embeddings

```python
# Manual test
from mcp_server.embeddings import generate_embedding, search_similar_embeddings

# Generate embeddings
emb1 = generate_embedding("machine learning algorithms")
emb2 = generate_embedding("deep learning neural networks")
emb3 = generate_embedding("cooking recipes")

# Test similarity
results = search_similar_embeddings(emb1, [(id1, emb2), (id2, emb3)])
# Should rank emb2 higher than emb3

print(f"Embedding 1 vs 2: {calculate_similarity(emb1, emb2)}")  # Should be ~0.9+
print(f"Embedding 1 vs 3: {calculate_similarity(emb1, emb3)}")  # Should be ~0.3
```

## Debugging

**Embedding not stored?**
- Check: `generate_embedding()` returns bytes
- Check: bytes are serializable (not corrupted)

**Search returning no results?**
- Check: `VECTOR_SIMILARITY_THRESHOLD` is not too high
- Check: Stored embeddings are not None/corrupted
- Lower threshold temporarily to debug

**Model loading slow?**
- First call always slow (downloads model)
- Subsequent calls cached and fast
- Preload on startup if needed: `get_embedding_model()` in `startup_event()`

**Memory usage high?**
- Model is ~100MB (normal)
- Consider lighter model: `all-MiniLM-L6-v2` (already using lightest)

## Future Enhancements

- [ ] Use different embedding model based on query type
- [ ] Cache query embeddings for repeated searches
- [ ] Batch embedding generation for bulk operations
- [ ] Hierarchical search (coarse-to-fine)
- [ ] User-specific embedding fine-tuning
