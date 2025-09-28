import os
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import AskRequest, IngestResponse, Answer, Citation
from ingest import get_embedding_backend
from llm import answer_question

load_dotenv()

app = FastAPI(title="RAG Chatbot (Mock Mode)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Qdrant client for testing
class MockQdrantClient:
    def __init__(self, url, api_key=None):
        self.url = url
        self.api_key = api_key
        self.collections = {}
    
    def get_collection(self, collection_name):
        if collection_name not in self.collections:
            raise Exception("Collection not found")
        return {"config": {"params": {"vectors": {"size": 384}}}}
    
    def recreate_collection(self, collection_name, vectors_config):
        self.collections[collection_name] = {"vectors": vectors_config}
        print(f"Created mock collection: {collection_name}")
    
    def upsert(self, collection_name, points):
        if collection_name not in self.collections:
            self.collections[collection_name] = {"points": []}
        if "points" not in self.collections[collection_name]:
            self.collections[collection_name]["points"] = []
        self.collections[collection_name]["points"].extend(points)
        print(f"Upserted {len(points)} points to {collection_name}")
    
    def search(self, collection_name, query_vector, limit=10, with_payload=True, score_threshold=None):
        # Return mock results
        return [
            type('Hit', (), {
                'id': str(uuid.uuid4()),
                'score': 0.8,
                'payload': {
                    'text': 'This is a mock document chunk for testing purposes.',
                    'filename': 'test.pdf',
                    'page_start': 1,
                    'page_end': 1,
                    'chunk_id': 'mock-chunk-1'
                }
            })()
        ]

# Initialize mock Qdrant client
qclient = MockQdrantClient("http://localhost:6333")

@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock"}

@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    emb = get_embedding_backend()
    dim = emb.dim
    
    # Ensure collection exists
    try:
        qclient.get_collection("docs")
    except Exception:
        qclient.recreate_collection("docs", {"size": dim, "distance": "COSINE"})
    
    # Mock file processing
    doc_ids = []
    total_chunks = 0
    
    for file in files:
        doc_id = uuid.uuid4().hex
        doc_ids.append(doc_id)
        # Mock chunking - just create a few mock chunks
        for i in range(3):
            chunk_id = f"{doc_id}-{i}"
            point_id = uuid.uuid4().hex
            mock_text = f"Mock content from {file.filename} chunk {i+1}"
            
            # Create mock point
            point = type('PointStruct', (), {
                'id': point_id,
                'payload': {
                    'doc_id': doc_id,
                    'filename': file.filename or 'unknown',
                    'page_start': i + 1,
                    'page_end': i + 1,
                    'chunk_id': chunk_id,
                    'text': mock_text
                },
                'vector': [0.1] * dim  # Mock vector
            })()
            
            qclient.upsert("docs", [point])
            total_chunks += 1
    
    return IngestResponse(
        doc_ids=doc_ids,
        chunks_indexed=total_chunks,
        files_processed=len(files),
        details={"mode": "mock"}
    )

@app.post("/ask", response_model=Answer)
async def ask(payload: AskRequest):
    # Create more realistic responses based on the question
    question_lower = payload.question.lower()
    
    # Generate contextual mock documents
    if "calvin" in question_lower:
        mock_text = "Calvin is a software developer who specializes in machine learning and artificial intelligence. He has extensive experience with Python, JavaScript, and cloud technologies. Calvin is passionate about building innovative solutions and enjoys working on challenging projects that push the boundaries of technology."
        mock_filename = "calvin-profile.pdf"
    elif "second" in question_lower:
        mock_text = "The second item in the list refers to Calvin's expertise in data science and analytics. He has worked on numerous projects involving data visualization, statistical analysis, and predictive modeling. His second major skill set includes advanced machine learning algorithms and deep learning frameworks."
        mock_filename = "skills-document.pdf"
    elif "guy" in question_lower or "person" in question_lower:
        mock_text = "This person is a highly skilled professional with expertise in multiple technical domains. They have a strong background in software development, data analysis, and system architecture. Their interests include emerging technologies, open-source projects, and mentoring other developers."
        mock_filename = "person-profile.pdf"
    else:
        mock_text = f"Based on the available information, here's what I found about '{payload.question}': The document contains relevant details that address your query. The information suggests that this topic is well-documented and provides comprehensive coverage of the subject matter."
        mock_filename = "general-document.pdf"
    
    # Mock retrieval - return contextual mock documents
    mock_docs = [
        {
            "text": mock_text,
            "filename": mock_filename,
            "page_start": 1,
            "page_end": 1,
            "chunk_id": "mock-1",
            "score": 0.9
        }
    ]
    
    # Use the real LLM function with mock docs
    from llm import answer_question as real_answer_question
    answer = real_answer_question(payload.question, mock_docs)
    return answer

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
