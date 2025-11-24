from __future__ import annotations
from typing import Dict
from app.models.model_router import ModelRouter
from app.utils.log_utils import log_info

SUPERVISOR_PROMPT = """
You are a supervisor orchestrating course file processing. Return JSON with keys: summarize_main (bool), follow_links (bool), max_links_to_follow (int), notes (string). Choose follow_links true when there are external references or embedded media. Keep max_links_to_follow between 0 and 5.
"""


def plan_for_file(filename: str, text_preview: str, links_count: int) -> Dict:
    router = ModelRouter()
    prompt = f"{SUPERVISOR_PROMPT}\nFile: {filename}\nPreview: {text_preview[:800]}\nLinks: {links_count}"
    result = router.complete(prompt, json_mode=True)
    output_text = result.get('output_text', '{}')
    try:
        plan = eval(output_text)
    except Exception:  # noqa: BLE001
        plan = {
            'summarize_main': True,
            'follow_links': links_count > 0,
            'max_links_to_follow': min(links_count, 3),
            'notes': 'Fallback supervisor decision',
        }
    log_info(f"Supervisor plan for {filename}: {plan}")
    return plan
