# main.py - Mendix MCP Memory Server
"""
FastAPI application with integrated SQLite persistence, vector embeddings, and auto-summarization
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import time
import logging
import uuid

# Import our modules
from models import StoreRequest, StoreResponse, SearchRequest, SearchResponse, MemoryResult, ListMemoriesResponse, MemoryDetail
from database import db
from summarization import summarize
from embeddings import generate_embedding, get_embedding_model, search_similar_embeddings, deserialize_embedding
from config import API_HOST, API_PORT, SEARCH_RESULTS_LIMIT, VECTOR_SIMILARITY_THRESHOLD

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Mendix MCP Memory Server",
    description="Persistent memory backend for Mendix AI agents",
    version="2.0",
)


# -------------------------
# Dependency: Ensure models are loaded
# -------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize models on startup"""
    logger.info("Starting MCP Memory Server")
    # Pre-load embedding model
    get_embedding_model()
    logger.info("Server ready")


# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/", tags=["health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "MCP Memory Server is running",
        "version": "2.0",
        "status": "healthy"
    }


@app.get("/health", tags=["health"])
async def health():
    """Detailed health check"""
    return {
        "status": "ok",
        "database": "connected",
        "embeddings": "ready"
    }


# -------------------------
# STORE_MEMORY - Main endpoint for storing conversations
# -------------------------
@app.post("/store_memory", response_model=StoreResponse, tags=["memory"])
async def store_memory(req: StoreRequest) -> StoreResponse:
    """
    Store a conversation message with auto-summarization and vector embedding

    Flow:
    1. Auto-summarize the content
    2. Generate vector embedding from summary
    3. Store in SQLite with metadata
    4. Return memory ID and summary

    Args:
        req: StoreRequest with user_id and content

    Returns:
        StoreResponse with memory ID, summary, and status
    """
    try:
        # Summarize the content
        summary = summarize(req.content)
        logger.info(f"Summarized {len(req.content)} chars to {len(summary)} chars for user {req.user_id}")

        # Generate vector embedding from summary
        embedding_bytes = generate_embedding(summary)

        # Generate unique memory ID
        memory_id = str(uuid.uuid4())

        # Store in database
        memory = db.add_memory(
            user_id=req.user_id,
            original_text=req.content,
            summary=summary,
            vector_embedding=embedding_bytes,
            conversation_id=None,
            message_type="user"
        )

        return StoreResponse(
            id=memory.id,
            summary=summary,
            status="stored"
        )

    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


# -------------------------
# SEARCH_MEMORY - Semantic search with vector embeddings
# -------------------------
@app.post("/search_memory", response_model=SearchResponse, tags=["memory"])
async def search_memory(req: SearchRequest) -> SearchResponse:
    """
    Search memories using semantic similarity with vector embeddings

    Flow:
    1. Generate embedding for search query
    2. Retrieve all user's memory embeddings from DB
    3. Calculate cosine similarity for each
    4. Return top-k sorted by similarity

    Args:
        req: SearchRequest with user_id, query, and limit

    Returns:
        SearchResponse with ranked results and similarity scores
    """
    try:
        # Generate query embedding
        query_embedding = generate_embedding(req.query)

        if query_embedding is None:
            logger.warning("Could not generate query embedding - falling back to all memories")
            # Fallback: return all user memories (no semantic search)
            memories = db.search_by_user(req.user_id, limit=req.limit)
            results = [
                MemoryResult(
                    id=m.id,
                    summary=m.summary,
                    similarity=1.0,
                    created_at=m.created_at
                )
                for m in memories
            ]
            return SearchResponse(results=results, total_found=len(results))

        # Get all stored embeddings for this user
        stored_embeddings = db.get_all_embeddings(req.user_id)

        if not stored_embeddings:
            logger.info(f"No memories found for user {req.user_id}")
            return SearchResponse(results=[], total_found=0)

        # Find similar embeddings
        similar = search_similar_embeddings(
            query_embedding,
            stored_embeddings,
            top_k=req.limit,
            threshold=VECTOR_SIMILARITY_THRESHOLD
        )

        # Fetch full memory details for results
        results = []
        for memory_id, similarity_score in similar:
            memory = db.get_memory_by_id(memory_id)
            if memory:
                results.append(
                    MemoryResult(
                        id=memory.id,
                        summary=memory.summary,
                        similarity=similarity_score,
                        created_at=memory.created_at
                    )
                )

        logger.info(f"Found {len(results)} similar memories for user {req.user_id}")
        return SearchResponse(results=results, total_found=len(results))

    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {str(e)}")


# -------------------------
# LIST_MEMORIES - Get all memories for a user
# -------------------------
@app.get("/memories/{user_id}", response_model=ListMemoriesResponse, tags=["memory"])
async def list_memories(user_id: str):
    """
    Retrieve all memories for a user

    Args:
        user_id: User identifier

    Returns:
        ListMemoriesResponse with all user memories
    """
    try:
        memories = db.search_by_user(user_id, limit=100)

        memory_details = [
            MemoryDetail(
                id=m.id,
                user_id=m.user_id,
                conversation_id=m.conversation_id,
                original_text=m.original_text,
                summary=m.summary,
                message_type=m.message_type,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in memories
        ]

        return ListMemoriesResponse(
            user_id=user_id,
            count=len(memory_details),
            memories=memory_details
        )

    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list memories: {str(e)}")


# -------------------------
# DELETE_MEMORY - Remove a specific memory
# -------------------------
@app.delete("/memories/{memory_id}", tags=["memory"])
async def delete_memory(memory_id: str):
    """
    Delete a specific memory by ID

    Args:
        memory_id: Memory identifier

    Returns:
        Confirmation of deletion
    """
    try:
        deleted = db.delete_memory(memory_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        logger.info(f"Deleted memory {memory_id}")
        return {"status": "deleted", "id": memory_id}

    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


# -------------------------
# STREAMING (SSE) - Server-Sent Events demo
# -------------------------
@app.get("/stream", tags=["streaming"])
async def stream():
    """
    Server-Sent Events streaming endpoint for agent integration

    Demonstrates streaming capability for chunked responses
    """
    def event_stream():
        for i in range(5):
            yield f"data: Memory chunk {i} processed\n\n"
            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# -------------------------
# Backward compatibility with V1
# -------------------------
@app.post("/store_memory_legacy", tags=["legacy"])
async def store_memory_legacy(content: dict):
    """Legacy endpoint for backward compatibility with V1"""
    req = StoreRequest(user_id=content.get("user_id"), content=content.get("content"))
    return await store_memory(req)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )