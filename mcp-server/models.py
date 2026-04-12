"""Pydantic models for API request/response validation"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class StoreRequest(BaseModel):
    """Request model for storing memories"""

    user_id: str = Field(..., description="User identifier")
    content: str = Field(..., description="Memory content to store")


class StoreResponse(BaseModel):
    """Response model after storing memory"""

    id: str = Field(..., description="Memory ID")
    summary: str = Field(..., description="Auto-generated summary")
    status: str = Field(..., description="Operation status")


class SearchRequest(BaseModel):
    """Request model for searching memories"""

    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="Search query")
    limit: int = Field(default=5, ge=1, le=20, description="Max results to return")


class MemoryResult(BaseModel):
    """Single memory result from search"""

    id: str = Field(..., description="Memory ID")
    summary: str = Field(..., description="Memory summary")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    created_at: datetime = Field(..., description="Creation timestamp")


class SearchResponse(BaseModel):
    """Response model for search results"""

    results: List[MemoryResult] = Field(..., description="List of matching memories")
    total_found: int = Field(..., description="Total results found")


class MemoryDetail(BaseModel):
    """Full memory details"""

    id: str
    user_id: str
    conversation_id: Optional[str]
    original_text: str
    summary: str
    message_type: str
    created_at: datetime
    updated_at: datetime


class ListMemoriesResponse(BaseModel):
    """Response for listing all user memories"""

    user_id: str
    count: int
    memories: List[MemoryDetail]
