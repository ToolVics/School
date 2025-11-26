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
        raw_value = data.get("raw_summary", "")
        if isinstance(raw_value, list):
            raw_value = "\n".join(str(item) for item in raw_value if item)
        elif not isinstance(raw_value, str):
            raw_value = str(raw_value)
        topics_value = data.get("topics", [])
        topics = topics_value if isinstance(topics_value, list) else []
        return {
            "raw_summary": raw_value,
            "topics": topics,
        }
    except json.JSONDecodeError:
        return {"raw_summary": str(payload), "topics": []}


def summarize_chunks(filename: str, text: str) -> Dict:
    router = ModelRouter()
    chunks = chunk_text(text)
    summaries: List[str] = []
    topics: List[str] = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        result = router.complete(f"{SUMMARY_PROMPT}\n\n{chunk}", json_mode=True, model=SUMMARY_MODEL)
        parsed = _parse_chunk_response(result.get("output_text", ""))
        raw_summary = parsed.get("raw_summary", "")
        if isinstance(raw_summary, list):
            raw_summary = "\n".join(str(item) for item in raw_summary if item)
        elif not isinstance(raw_summary, str):
            raw_summary = str(raw_summary)
        summaries.append(raw_summary)
        topics.extend(parsed.get("topics", []))
    raw_summary = "\n".join(filter(None, summaries))
    dedup_topics = list(dict.fromkeys([str(t) for t in topics if t]))[:10]
    log_info(f"Summaries generated for {filename}: {len(chunks)} chunks")
    return {
        "type": "raw_file",
        "filename": filename,
        "raw_summary": raw_summary,
        "topics": dedup_topics,
    }
