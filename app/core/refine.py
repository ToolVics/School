from __future__ import annotations
import json
from typing import Dict, List

from app.models.model_router import ModelRouter
from app.utils.log_utils import log_info

REFINE_PROMPT = """
You are refining course knowledge. Given raw summary and link insights, produce JSON with fields: filename, high_level_summary, key_points (list), learning_objectives (list), important_quotes (list), definitions (list), themes (list), topic_tags (list), inferred_insights (list).
"""


def refine_entry(filename: str, raw_summary: str, link_summaries: List[Dict]) -> Dict:
    router = ModelRouter()
    link_text = '\n'.join(item.get('content', '') for item in link_summaries)
    prompt = f"{REFINE_PROMPT}\nFILE: {filename}\nRAW SUMMARY:\n{raw_summary}\nLINK INSIGHTS:\n{link_text}"
    result = router.complete(prompt, json_mode=True)
    output_text = result.get('output_text', '{}')
    try:
        refined = json.loads(output_text)
    except json.JSONDecodeError:
        refined = {
            'filename': filename,
            'high_level_summary': raw_summary[:500],
            'key_points': raw_summary.split('\n')[:5],
            'learning_objectives': [],
            'important_quotes': [],
            'definitions': [],
            'themes': [],
            'topic_tags': [],
            'inferred_insights': [],
        }
    log_info(f"Refined entry for {filename}")
    return refined
