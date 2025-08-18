import os
from typing import List, Dict, Any
from openai import OpenAI
from models import Answer, Citation
from prompt import SYSTEM_PROMPT


def _format_citations(docs: List[Dict[str, Any]]) -> List[Citation]:
    out: List[Citation] = []
    for d in docs:
        out.append(
            Citation(
                filename=d.get("filename", ""),
                page_start=int(d.get("page_start", 0)),
                page_end=int(d.get("page_end", 0)),
                chunk_id=str(d.get("chunk_id", "")),
            )
        )
    return out


def _compose_context(docs: List[Dict[str, Any]]) -> str:
    lines = []
    for d in docs:
        meta = f"[{d.get('filename','')} p{d.get('page_start',0)}-{d.get('page_end',0)} | {d.get('chunk_id','')}]"
        text = d.get("text", "")
        lines.append(f"{meta}\n{text}")
    return "\n\n".join(lines)


def answer_question(question: str, docs: List[Dict[str, Any]]) -> Answer:
    # If no docs, return don't know
    if not docs:
        return Answer(answer="I don't know based on the provided context.", citations=[])

    ctx = _compose_context(docs)

    if os.getenv("OPENAI_API_KEY"):
        client = OpenAI()
        sys_prompt = SYSTEM_PROMPT
        user = (
            "Answer the user's question using ONLY the following context. "
            "If the answer isn't contained, say you don't know.\n\n"
            f"Context:\n{ctx}\n\nQuestion: {question}"
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
        return Answer(answer=content, citations=_format_citations(docs))

    # Stub deterministic template
    snippet = docs[0]["text"][:200].strip().replace("\n", " ")
    reply = (
        "[Stub LLM] Based on the context, here's a concise answer. "
        f"If uncertain, I say I don't know. Snippet: {snippet}"
    )
    return Answer(answer=reply, citations=_format_citations(docs))
