# 🚀 Quick Start Guide

## Option 1: Local Setup (Ollama) - Simplest ⚡

Perfect for development and testing. **Free, no API keys needed.**

### 1. Install Ollama
- Download from https://ollama.com/
- Install and start Ollama

### 2. Pull the model
```bash
ollama pull llama3.2
```

### 3. Copy `.env`
```bash
cp .env.example .env
```

### 4. Edit `.env` - ensure these are set:
```
UPSTASH_VECTOR_REST_URL=your_upstash_url
UPSTASH_VECTOR_REST_TOKEN=your_upstash_token
USE_GROQ=false
```

### 5. Run RAG
```bash
python rag_run.py
```

**That's it!** Ask questions about food. Ollama will run locally.

---

## Option 2: Cloud Setup (Groq) - Production Ready 🚀

Best for reliability, speed, and production. **Pay per token (~$0.05-0.79 per 1M tokens).**

### 1. Create Groq account
- Go to https://console.groq.com/
- Sign up (free account available)
- Go to https://console.groq.com/keys
- Copy your API key

### 2. Copy `.env`
```bash
cp .env.example .env
```

### 3. Edit `.env` - add these:
```
UPSTASH_VECTOR_REST_URL=your_upstash_url
UPSTASH_VECTOR_REST_TOKEN=your_upstash_token
USE_GROQ=true
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Run RAG
```bash
python rag_run.py
```

**That's it!** Groq will handle everything in the cloud.

---

## Switching Between Ollama and Groq

Just change one line in `.env`:

```bash
# Use Ollama (free, local)
USE_GROQ=false

# Use Groq (paid, cloud)
USE_GROQ=true
```

No code changes needed! The app detects it automatically.

---

## Groq Model Recommendations

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `llama-3.1-8b-instant` | 560 tps | Cheapest | Budget-conscious, speed is ok |
| `llama-3.3-70b-versatile` | 280 tps | Good | **Recommended** - best balance |
| `gpt-oss-120b` | 500 tps | Higher | Maximum quality |
| `gpt-oss-20b` | 1000 tps | Cheap | Speed + decent quality |

---

## Troubleshooting

### "Missing UPSTASH_VECTOR_REST_URL"
→ Make sure you set these in `.env` (not optional)

### "Ollama connection refused"
→ Make sure Ollama is running: `ollama serve`

### "Invalid GROQ_API_KEY"
→ Check your key at https://console.groq.com/keys

### "Rate limit exceeded"
→ You're using Groq and hit the free tier limit
→ Upgrade your tier or wait for reset

---

## Cost Examples

### Ollama (Local)
- **Monthly:** $0
- **Setup time:** 10 minutes

### Groq (Cloud)
- **100 queries/day with 1000 avg tokens:** ~$0.50/day (~$15/month)
- **Setup time:** 5 minutes
- **Benefit:** Always available, no local setup

---

## Next Steps

1. ✅ Choose Ollama or Groq
2. ✅ Add credentials to `.env`
3. ✅ Run `python rag_run.py`
4. ✅ Ask questions about food!

Questions? See the detailed docs:
- `README.md` - Full documentation
- `upstash_migration.md` - Vector DB details
- `groq_migration.md` - LLM migration guide
