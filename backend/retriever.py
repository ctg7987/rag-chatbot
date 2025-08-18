from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import CrossEncoder

from ingest import EmbeddingBackend

# Load cross-encoder once
_reranker = CrossEncoder("BAAI/bge-reranker-base")


def retrieve(qclient: QdrantClient, collection: str, question: str, emb: EmbeddingBackend) -> List[Dict[str, Any]]:
    # Embed question
    qvec = emb.embed_texts([question])[0]

    # Semantic search
    hits = qclient.search(
        collection_name=collection,
        query_vector=qvec,
        limit=24,
        with_payload=True,
        score_threshold=None,
    )

    if not hits:
        return []

    # Prepare for rerank
    pairs = [(question, h.payload.get("text", "")) for h in hits]
    scores = _reranker.predict(pairs)
    ranked = sorted(zip(hits, scores), key=lambda x: x[1], reverse=True)[:4]

    out = []
    for h, s in ranked:
        payload = h.payload or {}
        out.append({
            "text": payload.get("text", ""),
            "filename": payload.get("filename", ""),
            "page_start": int(payload.get("page_start", 0)),
            "page_end": int(payload.get("page_end", 0)),
            "chunk_id": payload.get("chunk_id", str(h.id)),
            "score": float(s),
        })
    return out
