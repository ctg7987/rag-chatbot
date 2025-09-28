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

    # Enhanced stub LLM with better responses
    context_text = docs[0]["text"]
    
    # Create a more natural response based on the context
    if len(context_text) > 100:
        # Extract key information from the context
        sentences = context_text.split('. ')
        if len(sentences) > 1:
            # Use the first meaningful sentence as the main answer
            main_answer = sentences[0] + "."
            if len(sentences) > 2:
                main_answer += " " + sentences[1] + "."
        else:
            main_answer = context_text[:300] + "..." if len(context_text) > 300 else context_text
    else:
        main_answer = context_text
    
    # Create a more natural response
    reply = f"Based on the available information: {main_answer}"
    
    return Answer(answer=reply, citations=_format_citations(docs))
