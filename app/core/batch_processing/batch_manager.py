from __future__ import annotations
from typing import Dict, List
from app.core.batch_processing.batch_chunker import chunk_text
from app.models.model_router import ModelRouter
from app.utils.log_utils import log_info

SUMMARY_PROMPT = """Summarize the provided course content chunk in 4 bullet points and extract 3-5 key topics as a JSON with fields raw_summary and topics."""


def summarize_chunks(filename: str, text: str) -> Dict:
    router = ModelRouter()
    chunks = chunk_text(text)
    summaries: List[str] = []
    topics: List[str] = []
    for chunk in chunks:
        result = router.complete(f"{SUMMARY_PROMPT}\n\n{chunk}", json_mode=False)
        summaries.append(result.get('output_text', ''))
        # naive topic extraction
        topics.extend([t.strip() for t in result.get('output_text', '').split('\n') if t.strip()])
    raw_summary = '\n'.join(summaries)
    dedup_topics = list(dict.fromkeys([t for t in topics if t]))[:10]
    log_info(f"Summaries generated for {filename}: {len(chunks)} chunks")
    return {
        'type': 'raw_file',
        'filename': filename,
        'raw_summary': raw_summary,
        'topics': dedup_topics,
    }
