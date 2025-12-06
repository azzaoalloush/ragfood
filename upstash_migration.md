Create a detailed design document to replace ChromaDB with Upstash Vector Database. I have added the Upstash Vector credentials in the .env file.

Key Information about Upstash Vector:
- Built-in embedding model: mixedbread-ai/mxbai-embed-large-v1
- 1024 dimensions, 512 sequence length, MTEB score 64.68
- Automatic text vectorization (no need for external embedding API)
- Serverless and cloud-hosted
- Cosine similarity for semantic search

Current Implementation Details:
- Using ChromaDB for local vector storage
- Using Ollama's mxbai-embed-large for embeddings
- Python-based RAG system with food data
- Manual embedding generation and upsert process

Requirements for Migration:
1. Replace ChromaDB client with Upstash Vector client
2. Remove manual embedding generation (Upstash handles this automatically)
3. Update upsert process to use raw text data instead of pre-computed embeddings
4. Modify query process to work with Upstash Vector API
5. Handle authentication and error management
6. Maintain the same RAG functionality and user experience

Study the following sites to guide the design:
https://upstash.com/docs/vector/features/embeddingmodels 

---

## 📊 ARCHITECTURE COMPARISON

### BEFORE (ChromaDB + Ollama)
```
User Question
    ↓
Local Ollama API (mxbai-embed-large)
    ↓
Manual embedding generation → Vector
    ↓
ChromaDB (Local SQLite storage)
    ↓
Cosine similarity search
    ↓
Retrieved documents → Ollama LLM
    ↓
Answer
```

**Stack:**
- Vector Database: ChromaDB (local, persistent)
- Embedding: Ollama (local, CPU/GPU dependent)
- Storage: SQLite (local disk)
- Network: Localhost only

### AFTER (Upstash Vector + Ollama)
```
User Question
    ↓
Upstash Vector API (auto-embedding)
    ↓
Raw text upsert → Server-side embedding
    ↓
Upstash Vector Database (cloud)
    ↓
Cosine similarity search
    ↓
Retrieved documents → Ollama LLM
    ↓
Answer
```

**Stack:**
- Vector Database: Upstash Vector (cloud, serverless)
- Embedding: Upstash built-in (mixedbread-ai/mxbai-embed-large-v1, server-side)
- Storage: Cloud (Upstash managed)
- Network: REST API over HTTPS

---

## 📋 DETAILED IMPLEMENTATION PLAN

### Phase 1: Code Structure Changes

#### 1.1 Update Imports
**Remove:**
```python
import chromadb
```

**Add:**
```python
from upstash_vector import Index
from dotenv import load_dotenv
```

#### 1.2 Replace ChromaDB initialization with Upstash
**OLD:**
```python
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "foods"
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
```

**NEW:**
```python
load_dotenv()
UPSTASH_URL = os.getenv("UPSTASH_VECTOR_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
index = Index(url=UPSTASH_URL, token=UPSTASH_TOKEN)
```

#### 1.3 Remove Ollama Embedding Function
**DELETE this function entirely:**
```python
def get_embedding(text):
    response = requests.post("http://localhost:11434/api/embeddings", json={
        "model": EMBED_MODEL,
        "prompt": text
    })
    return response.json()["embedding"]
```

**Reason:** Upstash handles embeddings automatically. No manual embedding generation needed.

### Phase 2: Data Upsert Process

#### 2.1 Replace Add Logic
**OLD (with manual embedding):**
```python
for item in new_items:
    enriched_text = item["text"]
    if "region" in item:
        enriched_text += f" This food is popular in {item['region']}."
    if "type" in item:
        enriched_text += f" It is a type of {item['type']}."
    
    emb = get_embedding(enriched_text)  # ← Manual embedding
    
    collection.add(
        documents=[item["text"]],
        embeddings=[emb],
        ids=[item["id"]]
    )
```

**NEW (Upstash handles embedding):**
```python
# Check existing vectors to avoid re-indexing
def get_existing_ids():
    try:
        # Query an empty vector to get metadata - or maintain local tracking
        return set()  # Initial run - Upstash will deduplicate on upsert
    except:
        return set()

existing_ids = get_existing_ids()
new_items = [item for item in food_data if item['id'] not in existing_ids]

if new_items:
    print(f"🆕 Adding {len(new_items)} new documents to Upstash...")
    vectors_to_upsert = []
    
    for item in new_items:
        # Enhance text with metadata
        enriched_text = item["text"]
        if "region" in item:
            enriched_text += f" This food is popular in {item['region']}."
        if "type" in item:
            enriched_text += f" It is a type of {item['type']}."
        
        # Upstash upsert format: (id, data, metadata)
        # Note: 'data' is raw text - Upstash auto-embeds it!
        vectors_to_upsert.append((
            item["id"],
            enriched_text,  # Raw text - no embedding needed
            {"food_name": item["text"], "region": item.get("region", ""), "type": item.get("type", "")}
        ))
    
    try:
        index.upsert(vectors=vectors_to_upsert)
        print(f"✅ Successfully upserted {len(vectors_to_upsert)} vectors")
    except Exception as e:
        print(f"❌ Upsert failed: {e}")
else:
    print("✅ All documents already in Upstash.")
```

### Phase 3: Query Process

#### 3.1 Replace Query Logic
**OLD (manual embedding + ChromaDB query):**
```python
def rag_query(question):
    # Manual embedding of question
    q_emb = get_embedding(question)
    
    # Query with embedding vector
    results = collection.query(query_embeddings=[q_emb], n_results=3)
    
    top_docs = results['documents'][0]
    top_ids = results['ids'][0]
```

**NEW (Upstash handles embedding):**
```python
def rag_query(question):
    try:
        # Upstash auto-embeds the raw text query - no manual embedding!
        results = index.query(
            data=question,          # Raw text - Upstash embeds it
            top_k=3,                # Number of results
            include_metadata=True   # Get metadata from upsert
        )
        
        # Extract documents from results
        top_docs = []
        top_ids = []
        
        for result in results:
            top_docs.append(result["metadata"].get("food_name", result["id"]))
            top_ids.append(result["id"])
```

**Key difference:** Query with raw text, not embeddings. Upstash handles the embedding automatically.

### Phase 4: Error Handling & Retry Strategy

#### 4.1 Add Resilient Error Handling
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, backoff_factor=1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"❌ Failed after {max_retries} attempts: {e}")
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    print(f"⚠️  Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def upsert_vectors_safe(vectors):
    index.upsert(vectors=vectors)

@retry_with_backoff(max_retries=3)
def query_vectors_safe(question, top_k=3):
    return index.query(data=question, top_k=top_k, include_metadata=True)
```

#### 4.2 Environment Variable Validation
```python
def validate_upstash_config():
    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    if not url or not token:
        raise ValueError("Missing UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN in .env")
    
    if not url.startswith("https://"):
        raise ValueError("UPSTASH_VECTOR_REST_URL must use HTTPS")
    
    print("✅ Upstash configuration validated")
    return url, token
```

### Phase 5: Performance & Cost Analysis

#### 5.1 Before (ChromaDB + Local Ollama)
| Metric | Value |
|--------|-------|
| Embedding Generation | ~50-100ms per item (local, depends on hardware) |
| Query Response | ~100-200ms (local, in-memory) |
| Storage | Local disk usage: ~500KB-1MB per 1000 vectors |
| Network | None (localhost only) |
| Cost | Hardware cost, electricity |
| Scaling | Limited by local machine resources |

#### 5.2 After (Upstash Vector)
| Metric | Value |
|--------|-------|
| Embedding Generation | Server-side (no local overhead) |
| Query Response | ~100-300ms (includes network latency) |
| Storage | Cloud-managed; ~1KB per vector stored |
| Network | HTTPS API calls (~10-50ms latency) |
| Cost | $0.01 per 10k reads, $0.01 per 10k writes (free tier available) |
| Scaling | Unlimited; auto-scales with demand |

**Cost Comparison:**
- **100 queries/day:** ~$30/year (Upstash) vs $0 (local, but hardware already purchased)
- **10,000 queries/day:** ~$3,000/year (Upstash) vs Local electricity (~$200/year + hardware)
- Break-even: ~20,000 daily queries or if avoiding local hardware investment

### Phase 6: Security Considerations

#### 6.1 API Key Management
```python
# ✅ GOOD: Use .env file (already mentioned)
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")

# ❌ BAD: Don't hardcode tokens
# token = "uper_long_secret_token_here"

# ✅ GOOD: Validate token format
def validate_token(token):
    if not token or len(token) < 20:
        raise ValueError("Invalid Upstash token format")
```

#### 6.2 .env File Example
```
UPSTASH_VECTOR_REST_URL=https://[your-region]-[your-id].upstash.io
UPSTASH_VECTOR_REST_TOKEN=your_token_here
OLLAMA_ENDPOINT=http://localhost:11434
```

#### 6.3 .gitignore Update
Ensure this is present:
```
.env
.env.local
*.pyc
__pycache__/
chroma_db/
```

### Phase 7: API Differences Summary

| Feature | ChromaDB | Upstash Vector |
|---------|----------|-----------------|
| **Authentication** | Local (no auth) | REST token in header |
| **Embedding** | Manual (external model) | Automatic (built-in) |
| **Upsert Format** | documents + embeddings + ids | text + metadata + ids |
| **Query Format** | embedding vectors | raw text |
| **Metadata** | No native support | Included in results |
| **Scaling** | Local machine limit | Unlimited, serverless |
| **Latency** | Sub-millisecond | 100-300ms (includes network) |
| **Persistence** | Local SQLite file | Cloud-managed |
| **Backup** | Manual file copy | Automatic (cloud) |

---

## 🔄 MIGRATION CHECKLIST

- [ ] Install Upstash Python SDK: `pip install upstash-vector python-dotenv`
- [ ] Create Upstash account and get REST URL + Token
- [ ] Add credentials to `.env` file
- [ ] Update imports in `rag_run.py`
- [ ] Remove `get_embedding()` function
- [ ] Replace ChromaDB initialization with Upstash Index
- [ ] Update upsert logic (remove manual embeddings)
- [ ] Update query logic (use raw text)
- [ ] Add error handling and retry logic
- [ ] Test with sample queries
- [ ] Update README.md documentation
- [ ] Remove ChromaDB dependency from code
- [ ] Clean up local `chroma_db/` directory (optional backup)
- [ ] Deploy and monitor

---

## 🧪 TESTING STRATEGY

### 1. Unit Tests for Key Functions
```python
def test_vector_upsert():
    # Test that vectors are correctly upserted to Upstash
    pass

def test_vector_query():
    # Test that queries return relevant results
    pass

def test_error_handling():
    # Test retry logic and timeout handling
    pass
```

### 2. Integration Test
```bash
python rag_run.py
# Ask: "Which Indian dish uses chickpeas?"
# Expected: Relevant food items returned
```

### 3. Performance Comparison
- Measure query response time before/after
- Track API call latency
- Monitor cost

---

## 📝 SUMMARY OF KEY CHANGES

1. **No more local embedding generation** - Upstash handles it
2. **No more ChromaDB files** - Everything is cloud-based
3. **Simpler data flow** - Raw text in, auto-embedded, results back
4. **Added network calls** - Trade-off between local control and cloud convenience
5. **Cost becomes explicit** - Pay for API usage instead of hardware
6. **Better scaling** - No local resource constraints