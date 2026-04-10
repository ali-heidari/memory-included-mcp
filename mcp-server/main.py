# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from memory import MemoryStore
from fastapi.responses import StreamingResponse
import time

app = FastAPI()
memory = MemoryStore()

# -------------------------
# Request Models
# -------------------------

class StoreRequest(BaseModel):
    user_id: str
    content: str

class SearchRequest(BaseModel):
    user_id: str
    query: str

# -------------------------
# MCP TOOLS
# -------------------------

@app.post("/store_memory")
async def store_memory(req: StoreRequest):
    memory.add(req.user_id, req.content)
    return {"status": "stored", "content": req.content}


@app.post("/search_memory")
async def search_memory(req: SearchRequest):
    results = memory.search(req.user_id, req.query)
    return {"results": results}


# -------------------------
# STREAMING (SSE)
# -------------------------

@app.get("/stream")
async def stream():
    def event_stream():
        for i in range(5):
            yield f"data: chunk {i}\n\n"
            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# -------------------------
# HEALTH CHECK
# -------------------------

@app.get("/")
async def root():
    return {"message": "MCP Memory Server is running"}