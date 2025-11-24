from __future__ import annotations
from typing import List
from app.config import DEFAULT_CHUNK_TARGET


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_TARGET) -> List[str]:
    words = text.split()
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if sum(len(w) + 1 for w in current) >= chunk_size:
            chunks.append(' '.join(current))
            current = []
    if current:
        chunks.append(' '.join(current))
    return chunks or [text]
