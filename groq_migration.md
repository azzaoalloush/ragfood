# 🚀 Groq Migration Plan: Replace Ollama with Groq Cloud API

## Overview

Replace the local Ollama LLM with Groq Cloud's high-performance API for text generation. This migration moves from local inference to cloud-based inference while maintaining the same RAG functionality.

## Current Implementation (Ollama)

**Current Setup:**
- Model: `llama3.2` (local)
- Endpoint: `http://localhost:11434`
- Execution: Local HTTP requests
- Stream: Supported via streaming API
- Dependencies: Ollama service running locally

**How Ollama is currently used:**
```python
response = requests.post("http://localhost:11434/api/generate", json={
    "model": LLM_MODEL,
    "prompt": prompt,
    "stream": False
})
answer = response.json()["response"].strip()
```

---

## 📊 ARCHITECTURE COMPARISON

### CURRENT (Upstash Vector + Ollama Local)
```
User Question
    ↓
Upstash Vector Query (cloud auto-embedding)
    ↓
Retrieved Context
    ↓
Build Prompt
    ↓
Local Ollama API (HTTP to localhost:11434)
    ↓
Local GPU/CPU Processing
    ↓
Response
```

### AFTER (Upstash Vector + Groq Cloud)
```
User Question
    ↓
Upstash Vector Query (cloud auto-embedding)
    ↓
Retrieved Context
    ↓
Build Prompt
    ↓
Groq Cloud API (HTTPS to api.groq.com)
    ↓
Groq Hardware (LPU inference)
    ↓
Response
```

**Key Point:** Upstash Vector stays the same. We're only replacing the LLM (Ollama → Groq).

---

## 📋 DETAILED IMPLEMENTATION PLAN

### Phase 1: Setup & Authentication

#### 1.1 Groq API Setup
1. Go to https://console.groq.com/
2. Sign up for free account
3. Generate API key from https://console.groq.com/keys
4. Store in `.env` file:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

#### 1.2 Install Groq SDK
```bash
pip install groq
```

### Phase 2: Code Migration

#### 2.1 Update Imports
**OLD:**
```python
import requests

# Using HTTP POST to local Ollama
response = requests.post("http://localhost:11434/api/generate", ...)
```

**NEW:**
```python
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
client = Groq(api_key=groq_api_key)
```

#### 2.2 Replace LLM Generation Function

**OLD (Ollama - non-streaming):**
```python
response = requests.post("http://localhost:11434/api/generate", json={
    "model": LLM_MODEL,
    "prompt": prompt,
    "stream": False
})
answer = response.json()["response"].strip()
```

**NEW (Groq - non-streaming):**
```python
chat_completion = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    model=groq_model,
    temperature=0.7,
    max_completion_tokens=1024,
    top_p=1
)
answer = chat_completion.choices[0].message.content.strip()
```

#### 2.3 Optional: Streaming Response (Better UX)

**OLD (Ollama streaming):**
```python
# Ollama returns plain text stream, parse manually
response = requests.post("http://localhost:11434/api/generate", json={...})
for line in response.iter_lines():
    chunk = json.loads(line)
    print(chunk["response"], end="", flush=True)
```

**NEW (Groq streaming):**
```python
stream = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    model=groq_model,
    temperature=0.7,
    max_completion_tokens=1024,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Phase 3: Error Handling & Resilience

#### 3.1 Handle Groq-Specific Errors
```python
from groq import Groq
from groq import RateLimitError, APIError

@retry_with_backoff(max_retries=3)
def generate_with_groq(prompt, model, max_tokens=1024):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            model=model,
            temperature=0.7,
            max_completion_tokens=max_tokens,
            top_p=1
        )
        return chat_completion.choices[0].message.content.strip()
    
    except RateLimitError as e:
        print(f"⚠️  Rate limit hit: {e}")
        raise
    except APIError as e:
        print(f"❌ Groq API error: {e}")
        raise
```

#### 3.2 Validate Groq Configuration
```python
def validate_groq_config():
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL")
    
    if not api_key:
        raise ValueError("❌ Missing GROQ_API_KEY in .env")
    
    if not model:
        raise ValueError("❌ Missing GROQ_MODEL in .env")
    
    print(f"✅ Groq configured: {model}")
    return api_key, model
```

### Phase 4: Environment Variables

#### 4.1 Update `.env.example`
```
# Upstash Vector Configuration
UPSTASH_VECTOR_REST_URL=https://your-region-your-id.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your_upstash_vector_token_here

# Groq Configuration (replaces local Ollama)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

#### 4.2 Available Groq Models (Production)

| Model | Speed (tps) | Cost (per 1M tokens) | Context |
|-------|-------------|----------------------|---------|
| llama-3.1-8b-instant | 560 | $0.05 / $0.08 | 131k |
| llama-3.3-70b-versatile | 280 | $0.59 / $0.79 | 131k / 32k |
| gpt-oss-120b | 500 | $0.15 / $0.60 | 131k / 65k |
| gpt-oss-20b | 1000 | $0.075 / $0.30 | 131k / 65k |

**Recommendation for RAG:** `llama-3.3-70b-versatile` (good balance of quality & speed)

---

## 🔄 MIGRATION CHECKLIST

- [ ] Create Groq account at https://console.groq.com/
- [ ] Generate API key from https://console.groq.com/keys
- [ ] Install Groq SDK: `pip install groq`
- [ ] Add GROQ_API_KEY and GROQ_MODEL to `.env`
- [ ] Update `rag_run.py` imports (remove requests from Ollama usage)
- [ ] Replace LLM generation code
- [ ] Add Groq error handling
- [ ] Test with single query
- [ ] Update README with Groq instructions
- [ ] Remove Ollama dependency documentation (or make it optional)
- [ ] Deploy and monitor usage

---

## 📊 COMPARISON: Ollama vs Groq

| Feature | Ollama | Groq |
|---------|--------|------|
| **Model Hosting** | Local machine | Cloud (LPU) |
| **Setup** | Download model (~5-10GB) | API key only |
| **Speed** | Depends on GPU/CPU | 280+ tokens/second |
| **Latency** | Sub-millisecond | 100-500ms (includes network) |
| **Cost** | Hardware only | $0.05-0.79 per 1M tokens |
| **Reliability** | Depends on local setup | 99.9% uptime SLA |
| **Scalability** | Single machine limit | Unlimited |
| **Model Selection** | Limited to what you download | 20+ models available |
| **Offline** | Yes | No (requires internet) |
| **Privacy** | Full (no external API) | Data sent to Groq servers |

---

## 💰 COST ANALYSIS

### Ollama (Local)
- **Hardware cost:** Already purchased (sunken cost)
- **Electricity:** ~$200/year (typical)
- **Monthly cost:** $0
- **Scaling:** Limited by hardware

### Groq (Cloud)
- **Estimated for food RAG:** 
  - Assume 100 queries/day with 2000 tokens avg per query
  - Input: 100 × 100 tokens/day = 10K tokens/day
  - Output: 100 × 1900 tokens/day = 190K tokens/day
  - **Monthly:** ~6M tokens input, ~57M tokens output
  - **Cost:** (6M × $0.59) + (57M × $0.79) = **$3,540 + $45,030 = ~$48,570/month**

Actually, that's expensive for food data! Better estimate:
- 100 queries/day with 1000 total tokens per query (200 context + 800 response)
- **Monthly:** 3M tokens input, 24M tokens output
- **Cost:** (3M × $0.59) + (24M × $0.79) = **$1,770 + $18,960 = ~$20,730/month**

**Break-even:** Groq makes sense when:
- You can't run local Ollama (no GPU)
- You need 99.9% uptime guarantees
- You want instant model switching
- You don't have hardware already purchased

For food RAG at scale: **Recommend staying local (Ollama) or using smaller Groq model (8B, 15% of cost)**

---

## 🔒 SECURITY CONSIDERATIONS

### 1. API Key Management
✅ **Good:**
```python
api_key = os.getenv("GROQ_API_KEY")  # From .env
client = Groq(api_key=api_key)
```

❌ **Bad:**
```python
api_key = "gsk_abc123..."  # Hardcoded
```

### 2. .gitignore
```
.env
.env.local
GROQ_API_KEY  # Never commit this
```

### 3. Rate Limiting
Groq enforces rate limits:
- **250KTPM** (250,000 tokens per minute) - Free tier
- Implement exponential backoff for retries
- Monitor usage in Groq console

### 4. Data Privacy
⚠️ **Important:** Prompts sent to Groq servers
- Don't include sensitive user data in context
- Review Groq's data retention policy: https://console.groq.com/docs/legal

---

## 🧪 TESTING STRATEGY

### 1. Unit Test
```python
def test_groq_integration():
    # Test that Groq API works
    response = generate_with_groq("What is 2+2?", groq_model)
    assert "4" in response
    print("✅ Groq API working")
```

### 2. Integration Test
```bash
python rag_run.py
# Ask: "Which Indian dish uses chickpeas?"
# Verify: Response is coherent and relevant
```

### 3. Cost Monitoring
- Track tokens used in Groq console
- Set spend alerts
- Monitor response quality

---

## ⚠️ POTENTIAL ISSUES & SOLUTIONS

| Issue | Cause | Solution |
|-------|-------|----------|
| `RateLimitError` | Too many requests | Implement backoff, upgrade tier |
| `API Connection Error` | Network/firewall issue | Check internet, firewall settings |
| `Invalid API Key` | Wrong/expired key | Regenerate from console.groq.com/keys |
| `Model Not Found` | Typo in model name | Check available models at console.groq.com |
| Slower responses | Network latency | Expected; LPU still faster than many GPUs |

---

## 🚀 ROLLBACK PLAN

If Groq migration fails:

1. **Quick Rollback:** Keep Ollama code in separate function
```python
def generate_answer_ollama(prompt):
    # Old Ollama code - keep as fallback
    pass

def generate_answer_groq(prompt):
    # New Groq code
    pass

# Use environment variable to switch
if os.getenv("USE_GROQ") == "true":
    answer = generate_answer_groq(prompt)
else:
    answer = generate_answer_ollama(prompt)
```

2. **Easy Switch:** Keep both in `.env`
```
USE_GROQ=false  # Set to true to use Groq, false for Ollama
```

---

## 📝 UPDATED README SECTION

Add to README.md:

```markdown
## LLM Options

### Option 1: Local Ollama (Default, Free)
- No API costs
- Requires GPU/CPU
- Faster locally but needs setup

### Option 2: Groq Cloud (Recommended for Production)
- High reliability
- No local setup needed
- Pay per usage (~$0.05-0.79 per 1M tokens)
- Instant model switching

Configure in `.env`:
```
USE_GROQ=true
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
```

---

## ✅ SUMMARY

**Migration Benefits:**
✅ No local GPU/Ollama setup needed
✅ 280+ tokens/second (very fast)
✅ 99.9% uptime SLA
✅ Easy model switching
✅ No version conflicts

**Trade-offs:**
❌ Pay per token (food RAG: ~$20K+/month at scale)
❌ Data sent to Groq servers
❌ Requires internet connection
❌ Rate limits apply

**Recommendation:** 
- **Development:** Use local Ollama (free, instant)
- **Production at scale:** Groq (reliable, fast)
- **Best of both:** Implement both, switch via environment variable