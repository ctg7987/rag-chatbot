import os
import uuid
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from pathlib import Path
from pydantic import BaseModel
from models import IngestResponse

from utils import normalize_text, parse_pdf_pages, approx_token_count


@dataclass
class EmbeddingBackend:
    name: str
    dim: int

    def embed_texts(self, texts: List[str]) -> List[List[float]]:  # pragma: no cover
        raise NotImplementedError


class OpenAIEmbeddingBackend(EmbeddingBackend):
    def __init__(self):
        self.client = OpenAI()
        # text-embedding-3-small -> 1536 dims
        self.model = "text-embedding-3-small"
        self.dim = 1536
        super().__init__(name="openai", dim=self.dim)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]


class MiniLMEmbeddingBackend(EmbeddingBackend):
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        # all-MiniLM-L6-v2 -> 384 dims
        super().__init__(name="minilm", dim=384)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embs = self.model.encode(texts, normalize_embeddings=True).tolist()
        return embs


def get_embedding_backend() -> EmbeddingBackend:
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddingBackend()
    return MiniLMEmbeddingBackend()


class Chunk(BaseModel):
    doc_id: str
    filename: str
    page_start: int
    page_end: int
    chunk_id: str
    text: str


def _chunk_text(text: str, target_tokens: int = 400, overlap_ratio: float = 0.2) -> List[str]:
    tokens = text.split()
    n = len(tokens)
    if n == 0:
        return []
    step = max(1, int(target_tokens * (1 - overlap_ratio)))
    out = []
    for start in range(0, n, step):
        end = min(n, start + target_tokens)
        out.append(" ".join(tokens[start:end]))
        if end == n:
            break
    return out


def _load_document(path: str, filename: str) -> List[Tuple[int, int, str]]:
    # Returns list of (page_start, page_end, text)
    ext = Path(filename).suffix.lower()
    texts = []
    if ext == ".pdf":
        pages = parse_pdf_pages(path)
        # Group into ranges for better chunk attribution (single page ranges)
        for pnum, content in pages:
            texts.append((pnum, pnum, content))
    elif ext in {".md", ".markdown", ".txt"}:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = normalize_text(f.read())
        texts.append((1, 1, content))
    else:
        # Fallback treat as text
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = normalize_text(f.read())
        texts.append((1, 1, content))
    return texts


def ingest_files(qclient: QdrantClient, collection: str, file_paths: List[Tuple[str, str]], emb: EmbeddingBackend):
    doc_ids: List[str] = []
    points: List[qmodels.PointStruct] = []
    total_chunks = 0

    for path, filename in file_paths:
        doc_id = uuid.uuid4().hex
        doc_ids.append(doc_id)
        spans = _load_document(path, filename)
        chunk_idx = 0
        for p_start, p_end, text in spans:
            text = normalize_text(text)
            if not text:
                continue
            chunks = _chunk_text(text)
            for chunk_text in chunks:
                chunk_id = f"{doc_id}-{chunk_idx}"
                point_id = uuid.uuid4().hex
                meta = {
                    "doc_id": doc_id,
                    "filename": filename,
                    "page_start": p_start,
                    "page_end": p_end,
                    "chunk_id": chunk_id,
                }
                points.append(
                    qmodels.PointStruct(
                        id=point_id,
                        payload=meta | {"text": chunk_text},
                        vector=[0.0] * emb.dim,  # placeholder, will set later
                    )
                )
                total_chunks += 1
                chunk_idx += 1

    # Embed in batches
    texts = [p.payload["text"] for p in points]
    vectors = emb.embed_texts(texts)
    for i, vec in enumerate(vectors):
        points[i].vector = vec

    if points:
        qclient.upsert(collection_name=collection, points=points)

    return IngestResponse(
        doc_ids=doc_ids,
        chunks_indexed=total_chunks,
        files_processed=len(file_paths),
    )
