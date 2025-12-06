import os
import json
import time
from functools import wraps
from dotenv import load_dotenv
from upstash_vector import Index
from groq import Groq

# Load environment variables
load_dotenv()

# Constants
JSON_FILE = "foods.json"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"

# Validate and setup Upstash Vector
def validate_upstash_config():
    url = os.getenv("UPSTASH_VECTOR_REST_URL")
    token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
    
    if not url or not token:
        raise ValueError("❌ Missing UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN in .env")
    
    if not url.startswith("https://"):
        raise ValueError("❌ UPSTASH_VECTOR_REST_URL must use HTTPS")
    
    print("✅ Upstash Vector configuration validated")
    return url, token

# Validate and setup Groq (if enabled)
def validate_groq_config():
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL")
    
    if not api_key:
        raise ValueError("❌ Missing GROQ_API_KEY in .env")
    
    if not model:
        raise ValueError("❌ Missing GROQ_MODEL in .env")
    
    print(f"✅ Groq configured: {model}")
    return Groq(api_key=api_key)

upstash_url, upstash_token = validate_upstash_config()
index = Index(url=upstash_url, token=upstash_token)

# Initialize Groq if enabled, otherwise Ollama
groq_client = None
if USE_GROQ:
    groq_client = validate_groq_config()
else:
    print("✅ Using local Ollama for LLM")

# Load data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    food_data = json.load(f)

# Retry decorator for resilient API calls
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

# Upsert vectors to Upstash
@retry_with_backoff(max_retries=3)
def upsert_vectors_safe(vectors):
    index.upsert(vectors=vectors)

# Add only new items to Upstash Vector
vectors_to_upsert = []
for item in food_data:
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
        enriched_text,  # Raw text - Upstash handles embedding
        {"food_name": item["text"], "region": item.get("region", ""), "type": item.get("type", "")}
    ))

if vectors_to_upsert:
    print(f"🆕 Upserting {len(vectors_to_upsert)} documents to Upstash Vector...")
    try:
        upsert_vectors_safe(vectors_to_upsert)
        print(f"✅ Successfully upserted {len(vectors_to_upsert)} vectors to Upstash")
    except Exception as e:
        print(f"❌ Failed to upsert vectors: {e}")
        raise
else:
    print("✅ No documents to upsert.")

# Query vectors from Upstash
@retry_with_backoff(max_retries=3)
def query_vectors_safe(question, top_k=3):
    return index.query(
        data=question,
        top_k=top_k,
        include_metadata=True
    )

# Generate answer with Groq
@retry_with_backoff(max_retries=3)
def generate_with_groq(prompt):
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant answering questions about food."},
            {"role": "user", "content": prompt}
        ],
        model=GROQ_MODEL,
        temperature=0.7,
        max_completion_tokens=1024,
        top_p=1
    )
    return chat_completion.choices[0].message.content.strip()

# Generate answer with local Ollama
@retry_with_backoff(max_retries=3)
def generate_with_ollama(prompt):
    import requests
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"].strip()

def rag_query(question):
    try:
        # Step 1: Query Upstash Vector (auto-embedding of question)
        results = query_vectors_safe(question, top_k=3)

        # Step 2: Extract documents from results
        top_docs = []
        top_ids = []
        
        for result in results:
            # Upstash returns: id, score, metadata
            top_ids.append(result["id"])
            top_docs.append(result["metadata"].get("food_name", result["id"]))

        # Step 3: Show friendly explanation of retrieved documents
        print("\n🧠 Retrieving relevant information to reason through your question...\n")

        for i, doc in enumerate(top_docs):
            print(f"🔹 Source {i + 1} (ID: {top_ids[i]}):")
            print(f"    \"{doc}\"\n")

        print("📚 These seem to be the most relevant pieces of information to answer your question.\n")

        # Step 4: Build prompt from context
        context = "\n".join(top_docs)

        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {question}
Answer:"""

        # Step 5: Generate answer with either Groq or Ollama
        if USE_GROQ and groq_client:
            print("🚀 Using Groq...\n")
            answer = generate_with_groq(prompt)
        else:
            print("⚙️  Using Ollama...\n")
            answer = generate_with_ollama(prompt)

        # Step 6: Return final results
        return answer
    
    except Exception as e:
        print(f"❌ Error during RAG query: {e}")
        raise


# Interactive loop
print("\n🧠 RAG is ready. Ask a question (type 'exit' to quit):\n")
while True:
    question = input("You: ")
    if question.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break
    try:
        answer = rag_query(question)
        print("🤖:", answer)
    except Exception as e:
        print(f"❌ Failed to process question: {e}")
