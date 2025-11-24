from __future__ import annotations
from typing import Dict, List, Tuple
from app.extractors.extract_text import extract_text_generic
from app.utils.log_utils import log_info


def extract_file(path: str) -> Tuple[str, List[str]]:
    text, links = extract_text_generic(path)
    log_info(f"Extracted {len(text)} characters and {len(links)} links from {path}")
    return text, links
