import os
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from models import AskRequest, IngestResponse, Answer, Citation
from ingest import ingest_files, get_embedding_backend
from retriever import retrieve
from llm import answer_question

load_dotenv()

app = FastAPI(title="RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "docs")

# Initialize Qdrant client
qclient = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    emb = get_embedding_backend()
    dim = emb.dim
    # Ensure collection exists with correct vector size
    exists = False
    try:
        info = qclient.get_collection(COLLECTION_NAME)
        exists = True
        if info.config.params.vectors.size != dim:
            return IngestResponse(
                doc_ids=[],
                chunks_indexed=0,
                files_processed=0,
                details={
                    "error": f"Existing collection vector size {info.config.params.vectors.size} != embedding dim {dim}. Please recreate collection or change embedding backend.",
                },
            )
    except Exception:
        exists = False
    if not exists:
        qclient.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
        )
    tmp_paths = []
    for f in files:
        # Save to temp path for simple processing
        ext = os.path.splitext(f.filename or "upload")[1]
        tmp = f"/tmp/{uuid.uuid4().hex}{ext}"
        content = await f.read()
        with open(tmp, "wb") as out:
            out.write(content)
        tmp_paths.append((tmp, f.filename or os.path.basename(tmp)))
    result = ingest_files(qclient, COLLECTION_NAME, tmp_paths, emb)
    # Cleanup temp files
    for p, _ in tmp_paths:
        try:
            os.remove(p)
        except Exception:
            pass
    return result


@app.post("/ask", response_model=Answer)
async def ask(payload: AskRequest):
    emb = get_embedding_backend()
    docs = retrieve(qclient, COLLECTION_NAME, payload.question, emb)
    answer = answer_question(payload.question, docs)
    return answer
