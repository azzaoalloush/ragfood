Here's a clear, beginner-friendly `README.md` for your RAG project, designed to explain what it does, how it works, and how someone can run it from scratch.

---

## 📄 `README.md`

````markdown
# 🧠 RAG-Food: Retrieval-Augmented Generation with Upstash Vector + Ollama

This is a **minimal working RAG (Retrieval-Augmented Generation)** demo using:

- ✅ Cloud vector database via [Upstash Vector](https://upstash.com/docs/vector/overview)
- ✅ Automatic embedding generation with `mixedbread-ai/mxbai-embed-large-v1`
- ✅ Local LLM via [Ollama](https://ollama.com/)
- ✅ A simple food dataset in JSON (Indian foods, fruits, etc.)

---

## 🎯 What This Does

This app allows you to ask questions like:

- “Which Indian dish uses chickpeas?”
- “What dessert is made from milk and soaked in syrup?”
- “What is masala dosa made of?”

It **does not rely on the LLM's built-in memory**. Instead, it:

1. **Stores your custom text data** (about food) in Upstash Vector
2. **Automatic embedding** with `mixedbread-ai/mxbai-embed-large-v1` (no manual setup needed)
3. For any question, it:
   - Upstash auto-embeds your question
   - Finds relevant context via semantic similarity search
   - Passes that context + question to a local LLM (`llama3.2`)
4. Returns a natural-language answer grounded in your data.

---

## 📦 Requirements

### ✅ Software

- Python 3.8+
- Ollama installed and running locally
- Upstash Vector account (free tier available)

### ✅ Ollama Models Needed

Run these in your terminal to install them:

```bash
ollama pull llama3.2
````

> Make sure `ollama` is running in the background. You can test it with:
>
> ```bash
> ollama run llama3.2
> ```

---

## 🛠️ Installation & Setup

### 1. Clone or download this repo

```bash
git clone https://github.com/yourname/rag-food
cd rag-food
```

### 2. Set up Upstash Vector

1. Go to [https://console.upstash.com/](https://console.upstash.com/)
2. Create a new Vector database
3. Select embedding model: `mixedbread-ai/mxbai-embed-large-v1`
4. Copy your REST URL and token

### 3. Configure environment variables

Copy `.env.example` to `.env` and add your Upstash credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:
```
UPSTASH_VECTOR_REST_URL=https://your-region-your-id.upstash.io
UPSTASH_VECTOR_REST_TOKEN=your_upstash_token_here
OLLAMA_ENDPOINT=http://localhost:11434
```

### 4. Install Python dependencies

```bash
pip install upstash-vector python-dotenv requests
```

### 5. Run the RAG app

```bash
python rag_run.py
```

On first run, it will:

* Load `foods.json`
* Upsert all items to Upstash Vector (auto-embedded)
* Start the interactive chat interface

---

## 📁 File Structure

```
rag-food/
├── rag_run.py           # Main app script
├── foods.json           # Food knowledge base
├── .env                 # Your credentials (add this)
├── .env.example         # Template for .env
├── README.md            # This file
└── upstash_migration.md # Migration guide (technical)
```

---

## 🧠 How It Works (Step-by-Step)

1. **Data** is loaded from `foods.json`
2. **Upstash automatically embeds** each entry using `mixedbread-ai/mxbai-embed-large-v1`
3. When you ask a question:
   - Upstash auto-embeds your question
   - The top 3 most relevant documents are retrieved
   - The context + question is passed to `llama3.2` running locally
   - The model answers using only that grounded context

---

## 🔄 Migration from ChromaDB

If you're coming from the ChromaDB version, see `upstash_migration.md` for:
- Architecture comparison
- Detailed API differences
- Performance & cost analysis
- Security considerations

---

## 🔍 Try Custom Questions

You can test the RAG in the interactive loop:

```
🧠 RAG is ready. Ask a question (type 'exit' to quit):

You: Which Indian dish uses chickpeas?
🤖: [Answer from your grounded context]
```

---

## 🚀 Next Ideas

* Swap in larger datasets (Wikipedia articles, recipes, PDFs)
* Add a web UI with Gradio or Flask
* Add metadata filtering for better search
* Use hybrid search (dense + sparse vectors)

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `UPSTASH_VECTOR_REST_URL` | Yes | REST API endpoint from Upstash console |
| `UPSTASH_VECTOR_REST_TOKEN` | Yes | API token from Upstash console |
| `OLLAMA_ENDPOINT` | No | Ollama API endpoint (defaults to `http://localhost:11434`) |

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `UPSTASH_VECTOR_REST_URL` | Yes | REST API endpoint from Upstash console |
| `UPSTASH_VECTOR_REST_TOKEN` | Yes | API token from Upstash console |
| `USE_GROQ` | No | Set to `true` to use Groq instead of Ollama |
| `GROQ_API_KEY` | If USE_GROQ=true | API key from https://console.groq.com/keys |
| `GROQ_MODEL` | No | Groq model name (defaults to `llama-3.3-70b-versatile`) |

### .gitignore

Make sure these are ignored:
```
.env
.env.local
*.pyc
__pycache__/
chroma_db/
```

### LLM Options

#### Option 1: Local Ollama (Default - Free)
Perfect for development and testing
- No API costs
- Requires local GPU/CPU
- Instant response times
- Full data privacy

**Setup:**
1. Install Ollama from https://ollama.com/
2. Run: `ollama pull llama3.2`
3. Start Ollama: `ollama serve`
4. Set `USE_GROQ=false` in `.env` (or leave it out)

#### Option 2: Groq Cloud (Production - Pay per Use)
Perfect for reliable, always-on service
- High performance (280+ tokens/second)
- 99.9% uptime SLA
- No local setup needed
- Pay only for what you use (~$0.05-0.79 per 1M tokens)

**Setup:**
1. Create account at https://console.groq.com/
2. Generate API key from https://console.groq.com/keys
3. Add to `.env`:
```
USE_GROQ=true
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
4. Run: `python rag_run.py`

**Model Options:**
- `llama-3.1-8b-instant` - Fast, cheap, 560 tokens/sec
- `llama-3.3-70b-versatile` - Balanced, 280 tokens/sec (recommended)
- `gpt-oss-120b` - Very capable, 500 tokens/sec
- `gpt-oss-20b` - Cost-effective, 1000 tokens/sec

---

## 👨‍🍳 Credits

Made by Callum using:

* [Upstash Vector](https://upstash.com/docs/vector/overview)
* [Ollama](https://ollama.com)
* [mixedbread-ai embeddings](https://www.mixedbread.ai/)
* Indian food inspiration 🍛

---

## 📝 License

MIT

