# RAG Chatbot Scaffold

Production-ready scaffold for a Retrieval-Augmented Generation (RAG) chatbot with FastAPI backend, Next.js frontend, and Qdrant vector store.

## Setup

Prereqs:
- Python 3.11+
- Node 18+
- Docker & Docker Compose

Env:
- Copy `backend/.env.example` to `.env` in repo root or export variables in shell.

```
cp backend/.env.example .env
```

## Run locally (Docker)

```
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Qdrant: http://localhost:6333

## API Endpoints

- GET /health
- POST /ingest (multipart/form-data with `files`)
- POST /ask { question, session_id? }

Responses:
- /ask returns JSON `{ "answer": string, "citations": [{ filename, page_start, page_end, chunk_id }] }`
- /ingest returns counts and `doc_ids`.

## Example curl

```
# health
curl -s http://localhost:8000/health | jq

# ingest
curl -s -F "files=@/path/to/doc.pdf" http://localhost:8000/ingest | jq

# ask
curl -s -X POST http://localhost:8000/ask \
	-H 'Content-Type: application/json' \
	-d '{"question":"What does the document say about X?"}' | jq
```

## Embeddings & LLM

- If `OPENAI_API_KEY` is present, embeddings use `text-embedding-3-small` and answers use `gpt-4o-mini`.
- Otherwise, embeddings use `sentence-transformers/all-MiniLM-L6-v2` and a deterministic stub LLM replies.

Collection name comes from env `COLLECTION_NAME` (default `docs`).

## Evaluation (RAGAS)

You can evaluate using RAGAS or similar frameworks. Export sampled questions, retrieved contexts, and answers, then compute metrics like faithfulness and answer relevancy.

## Switching models

- Embeddings: set/unset `OPENAI_API_KEY`.
- LLM: same; no key -> stub.

# rag-chatbot