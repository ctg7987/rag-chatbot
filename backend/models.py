from typing import List, Optional, Any
from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class Citation(BaseModel):
    filename: str
    page_start: int
    page_end: int
    chunk_id: str


class Answer(BaseModel):
    answer: str
    citations: List[Citation]
    session_id: Optional[str] = None


class IngestResponse(BaseModel):
    doc_ids: List[str]
    chunks_indexed: int
    files_processed: int
    details: Optional[Any] = None
