# Summarization Feature Context

## Feature Overview

Summarization reduces stored memory size while preserving semantic meaning, improving search efficiency and storage usage.

## Location
- **Main code**: `mcp_server/summarization.py`
- **Called from**: `mcp_server/main.py` (store_memory endpoint, before embedding)
- **Configuration**: `mcp_server/config.py` (length limits)

## How It Works

### Core Function (`summarize`)

```python
def summarize(text: str) -> str
```

**Purpose**: Convert long text into concise summary preserving key information

**Input**: Any text (conversation, notes, long-form content)  
**Output**: Shorter text (30-150 characters, configurable)

### Smart Fallback Strategy

Summarization uses a 3-tier fallback approach:

**Tier 1: Abstractive Summarization** (Preferred)
- Uses transformer model (if available)
- Generates new, concise text
- Preserves meaning
- Quality: High
- Speed: ~200-500ms

**Tier 2: Extractive Summarization** (Fallback)
- Extracts key sentences from original
- Doesn't generate new text
- Quality: Medium
- Speed: <10ms

**Tier 3: Truncation** (Final Fallback)
- Just truncates to max length
- Quality: Low
- Speed: <1ms
- Always succeeds

**Example Flow**:
```
Input: "I spent today learning about neural networks..."
  ↓
Try abstractive → Success! Returns concise summary
  ↓
Output: "Learning about neural networks and deep learning algorithms"
```

OR

```
Input: "The quick brown fox..."
  ↓
Try abstractive → Model not available
Try extractive → Extracts key phrases
  ↓
Output: "quick brown fox"
```

## Configuration

Set these in `config.py` or environment variables:

```python
# Length constraints
SUMMARIZATION_MAX_LENGTH = 150  # Maximum characters in summary
SUMMARIZATION_MIN_LENGTH = 30   # Minimum characters in summary

# Example rules by length
SUMMARY_RULES = {
    "short": {"min": 30, "max": 50},    # Texts <100 chars: short summary
    "medium": {"min": 50, "max": 100},  # Texts 100-500 chars: medium
    "long": {"min": 100, "max": 150},   # Texts >500 chars: long
}
```

## Integration in `/store_memory` Pipeline

```python
@app.post("/store_memory")
async def store_memory(req: StoreRequest) -> StoreResponse:
    # Step 1: Summarize
    summary = summarize(req.content)  # "This is a test..." → "Test conversation about..."
    
    # Step 2: Generate embedding from summary
    embedding_bytes = generate_embedding(summary)
    
    # Step 3: Store both original and summary
    memory = db.add_memory(
        user_id=req.user_id,
        original_text=req.content,      # Full original stored
        summary=summary,                 # Concise summary stored
        vector_embedding=embedding_bytes
    )
    
    return StoreResponse(id=memory.id, summary=summary)
```

**Why summarize before embedding?**
1. Reduces noise (removes filler words)
2. Improves embedding quality (focused content)
3. Faster search (less vector computation)
4. Storage efficient (smaller summaries)

## Benefits

| Aspect | Benefit |
|--------|---------|
| **Storage** | 70-90% reduction in summary text |
| **Search Quality** | Cleaner embeddings = better semantic matches |
| **Performance** | Smaller vectors = faster similarity comparisons |
| **Display** | Shows key info without overwhelming detail |

**Example**:
```
Original: "We discussed machine learning, neural networks, deep learning, 
          algorithms, training models, validation techniques, and how 
          to apply AI to real-world problems..."
          (140 characters)

Summary: "Machine learning, neural networks, and training techniques"
         (60 characters)
         
Reduction: 57% smaller while preserving meaning
```

## How Search Uses Summaries

```
User query: "machine learning"
  ↓
Search looks at stored SUMMARIES (not original text)
  ↓
Summary 1: "Machine learning neural networks..." → embedding generated
Summary 2: "Database design optimization..." → embedding generated
  ↓
Similarity scores calculated
  ↓
Results returned to user
```

**User gets summary + ability to see full original if needed**

## Models and Libraries

Current implementation uses:
- **transformers library** for abstractive summarization
- **nltk** for extractive summarization
- **Automatic fallback** if libraries unavailable

**Models**:
- Default: facebook/bart-large-cnn (high quality)
- Faster alternative: distilbart-cnn-6-6
- Lightweight alternative: pegasus-xsum

## Configuration Tips

### For Interview/Demo Dataset
```python
SUMMARIZATION_MAX_LENGTH = 150
SUMMARIZATION_MIN_LENGTH = 30
# Summarize everything for clean, professional display
```

### For Large Production Data
```python
SUMMARIZATION_MAX_LENGTH = 300
SUMMARIZATION_MIN_LENGTH = 50
# More permissive to preserve nuance in longer texts
```

### For Short Messages Only
```python
SUMMARIZATION_MAX_LENGTH = 80
SUMMARIZATION_MIN_LENGTH = 20
# Aggressive summarization for brevity
```

## Performance Characteristics

| Operation | Time |
|-----------|------|
| Abstractive summarization | 200-500ms (first call loads model) |
| Abstractive (cached) | 50-150ms |
| Extractive summarization | <10ms |
| Truncation | <1ms |

**Typical flow**:
- First memory stored: ~300ms (loads model)
- Subsequent memories: ~100-200ms each

## Fallback Chain Explained

```python
def summarize(text):
    try:
        # Try abstract summarization
        return abstractive_summarize(text)
    except ImportError:
        # transformers not installed, try extractive
        try:
            return extractive_summarize(text)
        except:
            # Fall back to truncation
            return truncate(text, MAX_LENGTH)
```

**Why this matters**: Service works even with partial dependencies

## Common Modifications

### Use Different Summarization Model
```python
# In summarization.py
model_name = "google/pegasus-xsum"  # Different model
# or
model_name = "t5-small"  # Smaller but faster

summarizer = pipeline("summarization", model=model_name)
```

### Change Summary Length
```python
# In config.py
SUMMARIZATION_MAX_LENGTH = 200  # Longer summaries
SUMMARIZATION_MIN_LENGTH = 40   # Shorter minimum
```

### Disable Summarization (testing only)
```python
# In summarization.py
def summarize(text):
    return text  # Return original, unmodified
```

## Testing Summarization

```python
from mcp_server.summarization import summarize

# Test short text
short = "Hello world"
print(summarize(short))  # Should pass through or minimal summary

# Test medium text
medium = "We discussed machine learning, deep learning, neural networks, and training algorithms in detail today."
print(summarize(medium))  # Should compress to ~80-120 chars

# Test long text
long = "Very long conversation about many topics..." * 10
print(summarize(long))  # Should compress to max length

# Test edge cases
print(summarize(""))  # Empty string
print(summarize("a" * 1000))  # Very long
```

## Debugging

**Summary is empty?**
- Check: Input text is not empty
- Check: MAX_LENGTH > MIN_LENGTH
- Check: Summarizer loaded successfully

**Summary too long?**
- Check: SUMMARIZATION_MAX_LENGTH setting
- Check: Truncation logic working

**Summarization slow?**
- First call always slow (model load)
- Subsequent calls cached
- Consider lighter model: distilbart-cnn-6-6

**Memory usage high?**
- Summarization models are ~1GB
- Loaded on first /store_memory call
- Consider lazy loading or preloading on startup

## Future Enhancements

- [ ] Support multiple summarization languages
- [ ] Configurable summary style (bullet points, paragraphs, etc.)
- [ ] Domain-specific summarizers (technical, casual, formal)
- [ ] User preference for summary length
- [ ] Bullet-point extraction instead of continuous text
- [ ] Summary quality scoring
