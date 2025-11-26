from __future__ import annotations
import json
from typing import Dict

from app.config import SUPERVISOR_MODEL
from app.models.model_router import ModelRouter
from app.utils.log_utils import log_info

SUPERVISOR_PROMPT = """
You are a supervisor orchestrating course file processing.
Infer the course theme, assignment purpose, instructor intent, and academic relevance of each link.
Determine whether the PDF is an excerpt, full chapter, or scanned copy and when OCR is unnecessary.
Return JSON with keys: summarize_main (bool), follow_links (bool), max_links_to_follow (int), notes (string).
Choose follow_links true when links appear academically relevant (citations, readings, media) and avoid navigation/login links.
Keep max_links_to_follow between 0 and 5.
"""


def plan_for_file(filename: str, text_preview: str, links_count: int) -> Dict:
    router = ModelRouter()
    prompt = f"{SUPERVISOR_PROMPT}\nFile: {filename}\nPreview: {text_preview[:800]}\nLinks: {links_count}"
    result = router.complete(prompt, json_mode=True, model=SUPERVISOR_MODEL)
    output_text = result.get('output_text', '{}')
    try:
        plan = json.loads(output_text)
    except json.JSONDecodeError:
        plan = {
            'summarize_main': True,
            'follow_links': links_count > 0,
            'max_links_to_follow': min(links_count, 3),
            'notes': 'Fallback supervisor decision',
        }
    log_info(f"Supervisor plan for {filename}: {plan}")
    return plan
