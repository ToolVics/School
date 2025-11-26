from __future__ import annotations
import json
from typing import Dict, List

from app.config import SUMMARY_MODEL
from app.core.batch_processing.batch_chunker import chunk_text
from app.models.model_router import ModelRouter
from app.utils.log_utils import log_info

SUMMARY_PROMPT = (
    "Summarize the provided course content chunk. Return JSON with keys "
    "raw_summary (3-5 bullet points) and topics (list of concise topic strings)."
)


def _parse_chunk_response(payload: str) -> Dict[str, List[str]]:
    try:
        data = json.loads(payload)
        return {
            "raw_summary": data.get("raw_summary", ""),
            "topics": data.get("topics", []) if isinstance(data.get("topics"), list) else [],
        }
    except json.JSONDecodeError:
        return {"raw_summary": payload, "topics": []}


def summarize_chunks(filename: str, text: str) -> Dict:
    router = ModelRouter()
    chunks = chunk_text(text)
    summaries: List[str] = []
    topics: List[str] = []
    for chunk in chunks:
        result = router.complete(f"{SUMMARY_PROMPT}\n\n{chunk}", json_mode=True, model=SUMMARY_MODEL)
        parsed = _parse_chunk_response(result.get("output_text", ""))
        summaries.append(parsed.get("raw_summary", ""))
        topics.extend(parsed.get("topics", []))
    raw_summary = "\n".join(filter(None, summaries))
    dedup_topics = list(dict.fromkeys([t for t in topics if t]))[:10]
    log_info(f"Summaries generated for {filename}: {len(chunks)} chunks")
    return {
        "type": "raw_file",
        "filename": filename,
        "raw_summary": raw_summary,
        "topics": dedup_topics,
    }
