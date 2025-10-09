"""
Enhanced RAG Chatbot Backend with:
- Conversation history & session management
- Streaming responses (SSE)
- Document management
- Error handling
- Logging
- Caching support
"""
import os
import uuid
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from pydantic import BaseModel

from models import AskRequest, IngestResponse, Answer, Citation
from ingest import ingest_files, get_embedding_backend
from retriever import retrieve
from llm import answer_question
from database import get_db

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Chatbot Enhanced",
    description="Production-ready RAG chatbot with conversation history and streaming",
    version="2.0.0"
)

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
try:
    qclient = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    logger.info(f"Connected to Qdrant at {QDRANT_URL}")
except Exception as e:
    logger.error(f"Failed to connect to Qdrant: {e}")
    qclient = None

# Initialize database
db = get_db()


# ==================== Models ====================

class SessionCreate(BaseModel):
    title: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str

class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    citations: List[dict]
    created_at: str

class DocumentResponse(BaseModel):
    doc_id: str
    filename: str
    file_size: int
    file_type: str
    chunks_count: int
    status: str
    uploaded_at: str

class AskRequestEnhanced(BaseModel):
    question: str
    session_id: Optional[str] = None
    use_history: bool = True


# ==================== Health & Stats ====================

@app.get("/health")
def health():
    """Health check endpoint"""
    try:
        stats = db.get_stats()
        return {
            "status": "ok",
            "database": "connected",
            "qdrant": "connected" if qclient else "disconnected",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "degraded", "error": str(e)}


@app.get("/stats")
def get_stats():
    """Get system statistics"""
    try:
        return db.get_stats()
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Session Management ====================

@app.post("/sessions", response_model=SessionResponse)
def create_session(payload: SessionCreate):
    """Create a new conversation session"""
    try:
        session_id = db.create_session(title=payload.title)
        session = db.get_session(session_id)
        logger.info(f"Created session: {session_id}")
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_model=List[SessionResponse])
def list_sessions(limit: int = Query(50, ge=1, le=100)):
    """List all conversation sessions"""
    try:
        sessions = db.list_sessions(limit=limit)
        return sessions
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """Get session details"""
    try:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session and all its messages"""
    try:
        db.delete_session(session_id)
        logger.info(f"Deleted session: {session_id}")
        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: str, limit: int = Query(100, ge=1, le=500)):
    """Get all messages for a session"""
    try:
        messages = db.get_messages(session_id, limit=limit)
        return messages
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Document Management ====================

@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    if not qclient:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    
    try:
        emb = get_embedding_backend()
        dim = emb.dim
        
        # Ensure collection exists
        exists = False
        try:
            info = qclient.get_collection(COLLECTION_NAME)
            exists = True
            if info.config.params.vectors.size != dim:
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection vector size mismatch: {info.config.params.vectors.size} != {dim}"
                )
        except Exception:
            exists = False
        
        if not exists:
            qclient.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
            )
            logger.info(f"Created collection: {COLLECTION_NAME}")
        
        # Save files temporarily
        tmp_paths = []
        doc_ids = []
        
        for f in files:
            ext = os.path.splitext(f.filename or "upload")[1]
            tmp = f"/tmp/{uuid.uuid4().hex}{ext}"
            content = await f.read()
            
            with open(tmp, "wb") as out:
                out.write(content)
            
            tmp_paths.append((tmp, f.filename or os.path.basename(tmp)))
            
            # Add document to database
            doc_id = uuid.uuid4().hex
            doc_ids.append(doc_id)
            db.add_document(
                doc_id=doc_id,
                filename=f.filename or "unknown",
                file_size=len(content),
                file_type=ext,
                metadata={"original_name": f.filename}
            )
        
        # Process files
        result = ingest_files(qclient, COLLECTION_NAME, tmp_paths, emb)
        
        # Update document status
        for i, doc_id in enumerate(doc_ids):
            chunks_per_doc = result.chunks_indexed // len(doc_ids)  # Approximate
            db.update_document_status(doc_id, "completed", chunks_per_doc)
        
        # Cleanup temp files
        for p, _ in tmp_paths:
            try:
                os.remove(p)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {p}: {e}")
        
        logger.info(f"Ingested {len(files)} files, {result.chunks_indexed} chunks")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents", response_model=List[DocumentResponse])
def list_documents(status: Optional[str] = None):
    """List all uploaded documents"""
    try:
        documents = db.list_documents(status=status)
        return documents
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str):
    """Get document details"""
    try:
        document = db.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Delete a document (metadata only, vectors remain in Qdrant)"""
    try:
        # TODO: Also delete from Qdrant by filtering on doc_id
        db.delete_document(doc_id)
        logger.info(f"Deleted document: {doc_id}")
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Chat / Ask ====================

@app.post("/ask", response_model=Answer)
async def ask(payload: AskRequestEnhanced):
    """Ask a question (with optional conversation history)"""
    if not qclient:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    
    try:
        # Get or create session
        session_id = payload.session_id or str(uuid.uuid4())
        if not db.get_session(session_id):
            db.create_session(session_id, title=f"Chat {session_id[:8]}")
        
        # Save user message
        db.add_message(session_id, "user", payload.question)
        
        # Get conversation context if enabled
        context_prefix = ""
        if payload.use_history:
            context = db.get_conversation_context(session_id, max_messages=6)
            if context:
                context_prefix = f"Previous conversation:\n{context}\n\nCurrent question: "
        
        # Retrieve relevant documents
        emb = get_embedding_backend()
        question_with_context = context_prefix + payload.question if context_prefix else payload.question
        docs = retrieve(qclient, COLLECTION_NAME, question_with_context, emb)
        
        # Generate answer
        answer = answer_question(payload.question, docs)
        
        # Save assistant message
        citations_dict = [c.dict() for c in answer.citations]
        db.add_message(session_id, "assistant", answer.answer, citations_dict)
        
        logger.info(f"Answered question in session {session_id}")
        
        # Add session_id to response
        return Answer(
            answer=answer.answer,
            citations=answer.citations,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/stream")
async def ask_stream(payload: AskRequestEnhanced):
    """Ask a question with streaming response (SSE)"""
    if not qclient:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    
    async def generate():
        try:
            # Get or create session
            session_id = payload.session_id or str(uuid.uuid4())
            if not db.get_session(session_id):
                db.create_session(session_id, title=f"Chat {session_id[:8]}")
            
            # Save user message
            db.add_message(session_id, "user", payload.question)
            
            # Get conversation context
            context_prefix = ""
            if payload.use_history:
                context = db.get_conversation_context(session_id, max_messages=6)
                if context:
                    context_prefix = f"Previous conversation:\n{context}\n\nCurrent question: "
            
            # Retrieve documents
            emb = get_embedding_backend()
            question_with_context = context_prefix + payload.question if context_prefix else payload.question
            docs = retrieve(qclient, COLLECTION_NAME, question_with_context, emb)
            
            # Generate answer (for now, send as single chunk)
            # TODO: Implement actual streaming from LLM
            answer = answer_question(payload.question, docs)
            
            # Stream response
            import json
            response_data = {
                "answer": answer.answer,
                "citations": [c.dict() for c in answer.citations],
                "session_id": session_id
            }
            
            # Save assistant message
            db.add_message(session_id, "assistant", answer.answer, response_data["citations"])
            
            yield f"data: {json.dumps(response_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

