# Coding Standards and Patterns

## Pydantic Model Pattern

All API inputs and outputs use Pydantic models for validation.

**Pattern**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MyRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    content: str = Field(..., min_length=1)
    optional_field: Optional[str] = None

class MyResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
```

**Rules**:
- Every API endpoint has corresponding `Request` and `Response` models
- Use `Field()` for validation and documentation
- Use `Optional[]` for nullable fields
- Keep models in `mcp_server/models.py`
- Leverage Pydantic for automatic validation (don't manually check in endpoints)

**Benefits**:
- Auto-generated OpenAPI docs
- Type safety
- Automatic JSON serialization
- IDE autocompletion

---

## Database Layer Pattern (SQLAlchemy)

**Pattern**:
```python
from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.orm import Session
from datetime import datetime

# Define model
class MyRecord(Base):
    __tablename__ = "my_table"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# CRUD operation
def add_record(session: Session, data: dict):
    record = MyRecord(**data)
    session.add(record)
    session.commit()
    return record
```

**Rules**:
- Use SQLAlchemy ORM, not raw SQL
- Index frequently queried fields (e.g., `user_id`)
- Include `created_at` and `updated_at` timestamps on all records
- Use UUID strings for IDs
- Keep database code in `mcp_server/database.py`
- Use context managers for sessions: `with Session(engine) as session:`

---

## API Endpoint Pattern

**Pattern**:
```python
from fastapi import FastAPI, HTTPException
from .models import MyRequest, MyResponse

app = FastAPI()

@app.post("/my_endpoint", response_model=MyResponse, tags=["category"])
async def my_endpoint(req: MyRequest) -> MyResponse:
    """
    Brief description of what endpoint does.
    
    Flow:
    1. Validate input
    2. Process data
    3. Store/retrieve from DB
    4. Return response
    """
    try:
        # Business logic
        result = process(req)
        return MyResponse(id=result.id, status="success")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Rules**:
- Use type hints for parameters and return values
- Include docstring explaining flow
- Always validate inputs (Pydantic does this)
- Catch exceptions and log them
- Return appropriate HTTP status codes
- Use `response_model=` to enforce response shape
- Organize endpoints by `tags=` for documentation

---

## Error Handling Pattern

**Pattern**:
```python
try:
    # Operation that might fail
    result = do_something()
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database operation failed")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

**Rules**:
- Catch specific exceptions first, generic last
- Log all errors with context
- Return meaningful error messages
- Use appropriate HTTP status codes:
  - 400: Bad input (validation failed)
  - 404: Resource not found
  - 500: Internal server error
- Never expose internal stack traces to client

---

## Configuration Pattern

All settings go in `mcp_server/config.py`:

```python
import os
from pathlib import Path

# Database
DB_PATH = os.getenv("DB_PATH", "memory.db")
DB_URL = f"sqlite:///{DB_PATH}"

# Embeddings
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
VECTOR_SIMILARITY_THRESHOLD = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.7"))

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
```

**Rules**:
- Define all config values once
- Use environment variables for deployment flexibility
- Provide sensible defaults
- Never hardcode values in code
- Import from config throughout codebase

---

## Logging Pattern

```python
import logging

logger = logging.getLogger(__name__)

# In functions
logger.info(f"Processing memory for user {user_id}")
logger.error(f"Failed to generate embedding: {e}")
logger.warning(f"Similarity threshold not met: {score} < {threshold}")
```

**Rules**:
- Create logger per module: `logger = logging.getLogger(__name__)`
- Log significant operations (not every line)
- Include context: user_id, record_id, query, etc.
- Use appropriate level: info, warning, error
- Never log sensitive data (passwords, keys)

---

## Import Pattern

Keep imports organized:

```python
# Standard library
from datetime import datetime
from typing import List, Optional

# Third-party
from sqlalchemy import Column, String
from pydantic import BaseModel

# Local
from .config import DB_URL
from .models import StoreRequest
```

**Rules**:
- Group imports: stdlib → third-party → local
- Use relative imports within package (`.config`)
- Use absolute imports outside package
- Avoid circular imports (rethink module structure if occurring)

---

## Type Hints Pattern

Always use type hints:

```python
# Good
def search_memories(user_id: str, query: str, limit: int = 5) -> List[dict]:
    pass

# Bad
def search_memories(user_id, query, limit=5):
    pass
```

**Benefits**:
- IDE autocompletion
- Type checking with mypy
- Self-documenting code
- Easier refactoring

---

## Testing Pattern

Tests should mirror the module structure:

```
mcp_server/
  database.py
  embeddings.py
  
tests/
  test_database.py
  test_embeddings.py
```

Each test:
1. Sets up fixtures (test data)
2. Calls function under test
3. Asserts expected behavior
4. Cleans up

---

## Code Review Checklist

Before committing:
- ✅ Pydantic models for all API inputs/outputs
- ✅ SQLAlchemy for all database access
- ✅ Error handling with appropriate status codes
- ✅ Logging with context
- ✅ Type hints throughout
- ✅ Configuration via config.py
- ✅ Tests for new functionality
- ✅ Documentation updated
