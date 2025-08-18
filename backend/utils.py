import re
from typing import List, Tuple
from pypdf import PdfReader


def normalize_text(text: str) -> str:
    text = text.replace("\u00A0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_pdf_pages(path: str) -> List[Tuple[int, str]]:
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        content = page.extract_text() or ""
        pages.append((i + 1, normalize_text(content)))
    return pages

# Simple approximate token count by whitespace; replace with tiktoken for GPT counts if needed
# We keep it minimal and dependency-light here.

def approx_token_count(text: str) -> int:
    return max(1, len(text.split()))
