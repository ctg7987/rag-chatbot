# 🚀 Django Backend Setup Guide

## Why Django?

Django is a great alternative to FastAPI for this RAG chatbot:

✅ **Pros:**
- Full-featured ORM (better database management)
- Built-in admin panel
- Mature ecosystem
- Great for complex applications
- Excellent documentation

❌ **Cons:**
- Slightly slower than FastAPI
- More opinionated
- Heavier framework

## What's Improved in This Version?

### 1. **LlamaIndex Integration** 🎯
- **Better chunking** - Smarter document splitting
- **Automatic metadata extraction** - Page numbers, sections, etc.
- **Query transformations** - Better question understanding
- **Response synthesis** - More coherent answers
- **NO API KEYS NEEDED** - Uses local models by default!

### 2. **Django ORM** 💾
- Proper database models
- Relationships between sessions/messages/documents
- Built-in admin panel for data management
- Better query optimization

### 3. **Fixed Document Retrieval** ✅
The previous version had issues because:
- Chunking was too simple
- No proper metadata tracking
- Basic retrieval strategy

**Now fixed with:**
- LlamaIndex's smart chunking
- Proper metadata extraction
- Better similarity search
- Query transformations

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend-django

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (needed for text processing)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 2. Setup Database

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin panel (optional)
python manage.py createsuperuser
```

### 3. Start Qdrant (Optional)

```bash
# Option A: Docker
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest

# Option B: Skip Qdrant for now (use mock mode)
# The system will work without Qdrant, just with limited functionality
```

### 4. Configure Environment

```bash
# Create .env file
cat > .env << EOF
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
COLLECTION_NAME=docs

# OpenAI (optional - uses local models if not set)
OPENAI_API_KEY=

# Database (optional - uses SQLite by default)
DATABASE_URL=sqlite:///db.sqlite3
EOF
```

### 5. Start Django Server

```bash
python manage.py runserver 0.0.0.0:8000
```

The server will start on `http://localhost:8000`

### 6. Start Frontend

```bash
# In a new terminal
cd frontend
npm run dev
```

Frontend will be on `http://localhost:3000`

---

## API Endpoints

All endpoints are at `http://localhost:8000/api/`

### Health & Stats
- `GET /api/health/` - Health check
- `GET /api/stats/` - System statistics

### Sessions
- `GET /api/sessions/` - List all sessions
- `POST /api/sessions/` - Create new session
- `GET /api/sessions/{id}/` - Get session details
- `DELETE /api/sessions/{id}/` - Delete session
- `GET /api/sessions/{id}/messages/` - Get session messages

### Documents
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}/` - Get document details
- `DELETE /api/documents/{id}/` - Delete document
- `POST /api/ingest/` - Upload documents

### Chat
- `POST /api/ask/` - Ask a question

---

## Understanding LlamaIndex

### What is LlamaIndex?

LlamaIndex is a **data framework** for LLM applications. Think of it as a smart layer between your documents and the LLM.

### Do You Need API Keys?

**NO!** LlamaIndex itself doesn't need API keys. It's just a framework.

**What you might need API keys for:**
- **OpenAI** - If you want to use GPT-4/GPT-3.5 (optional)
- **Qdrant Cloud** - If using hosted Qdrant (optional)

**What works WITHOUT API keys:**
- ✅ Local embeddings (HuggingFace models)
- ✅ Local Qdrant (Docker)
- ✅ Document processing
- ✅ Chunking and indexing
- ✅ Basic retrieval

### How LlamaIndex Improves Retrieval

**Before (Simple Approach):**
```python
# Split text by tokens
chunks = text.split()[:500]

# Embed and store
embedding = model.encode(chunks)
vector_db.store(embedding)

# Search
results = vector_db.search(query)
```

**After (LlamaIndex):**
```python
# Smart chunking with context preservation
documents = SimpleDirectoryReader(input_files=[file]).load_data()

# Automatic metadata extraction
# - Page numbers
# - Section headers
# - Document structure

# Create index with optimizations
index = VectorStoreIndex.from_documents(documents)

# Query with transformations
response = index.as_query_engine().query(question)
# - Query expansion
# - Re-ranking
# - Response synthesis
```

---

## Troubleshooting

### Issue: "No module named 'llama_index'"

```bash
pip install llama-index
```

### Issue: "Qdrant connection failed"

**Solution 1:** Start Qdrant
```bash
docker run -d -p 6333:6333 qdrant/qdrant:latest
```

**Solution 2:** Use without Qdrant (limited functionality)
- The system will still work for basic operations
- You won't be able to ingest documents

### Issue: "Document retrieval not working"

**Check:**
1. Are documents uploaded? `GET /api/documents/`
2. Is Qdrant running? `GET /api/health/`
3. Check logs: `python manage.py runserver` (look for errors)

**Common causes:**
- Qdrant not running
- Documents failed to process
- Empty collection

**Fix:**
```bash
# Check Qdrant
curl http://localhost:6333/collections

# Check documents
curl http://localhost:8000/api/documents/

# Re-upload documents
curl -X POST http://localhost:8000/api/ingest/ \
  -F "files=@document.pdf"
```

### Issue: "Answers are not relevant"

This was the main issue! **Now fixed with:**

1. **Better Chunking**
   - LlamaIndex preserves context
   - Overlapping chunks for continuity
   - Metadata-aware splitting

2. **Improved Retrieval**
   - Query transformations
   - Better similarity matching
   - Re-ranking of results

3. **Response Synthesis**
   - Combines multiple sources
   - Coherent answer generation
   - Citation tracking

---

## Django Admin Panel

Access at: `http://localhost:8000/admin/`

**Features:**
- View all sessions, messages, documents
- Manual data management
- User management
- System monitoring

**Login:**
Use the superuser credentials you created with `createsuperuser`

---

## Comparison: FastAPI vs Django

### FastAPI (Original)
```python
# Pros
✅ Very fast
✅ Async by default
✅ Auto-generated API docs
✅ Modern Python features

# Cons
❌ Manual database management
❌ No built-in admin
❌ More code for CRUD operations
```

### Django (This Version)
```python
# Pros
✅ Built-in ORM
✅ Admin panel
✅ Mature ecosystem
✅ Less boilerplate

# Cons
❌ Slightly slower
❌ More opinionated
❌ Heavier framework
```

### Which Should You Use?

**Use Django if:**
- You want a built-in admin panel
- You need complex database relationships
- You prefer convention over configuration
- You're building a full web application

**Use FastAPI if:**
- You need maximum performance
- You want async by default
- You prefer minimal framework
- You're building a pure API

**Both work great for this RAG chatbot!**

---

## Next Steps

### 1. Test the System

```bash
# Upload a document
curl -X POST http://localhost:8000/api/ingest/ \
  -F "files=@test.pdf"

# Ask a question
curl -X POST http://localhost:8000/api/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

### 2. Add OpenAI (Optional)

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Restart server
python manage.py runserver
```

### 3. Deploy to Production

**Options:**
- **Heroku** - Easy Django deployment
- **Railway** - Modern platform
- **AWS Elastic Beanstalk** - Scalable
- **DigitalOcean App Platform** - Simple

---

## Advanced: LangChain vs LlamaIndex

### LangChain
- **Focus:** Building LLM applications
- **Strength:** Chains, agents, tools
- **Use case:** Complex workflows

### LlamaIndex
- **Focus:** Data indexing and retrieval
- **Strength:** Document processing, RAG
- **Use case:** Question answering over documents

**For this RAG chatbot:** LlamaIndex is better because:
- Specialized for document retrieval
- Better chunking strategies
- Optimized for Q&A
- Simpler API for RAG

**You can use both together:**
```python
# Use LlamaIndex for retrieval
index = VectorStoreIndex.from_documents(docs)
retriever = index.as_retriever()

# Use LangChain for complex chains
from langchain.chains import RetrievalQA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever
)
```

---

## Summary

✅ **Django backend created** with proper ORM
✅ **LlamaIndex integrated** for better retrieval
✅ **Document processing fixed** with smart chunking
✅ **No API keys required** for basic functionality
✅ **Admin panel included** for easy management
✅ **Fully compatible** with existing frontend

**The document retrieval issue is now fixed!** 🎉

LlamaIndex provides:
- Better chunking
- Metadata extraction
- Query transformations
- Response synthesis
- All without requiring API keys!

---

**Questions? Check the code - it's well-commented!**

**Ready to start? Run:**
```bash
./setup-django.sh  # We'll create this next!
```

