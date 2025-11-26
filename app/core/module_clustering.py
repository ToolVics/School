from __future__ import annotations
import json
from typing import Dict, List

from app.models.model_router import ModelRouter
from app.config import MODULES_PATH, CLUSTER_MODEL
from app.utils.file_utils import ensure_dir
from app.utils.log_utils import log_info

MODULE_PROMPT = """
Cluster the provided course files into 4-10 modules. Return JSON {"modules": [{"title":...,"description":...,"topics_included":[],"summary":...}]}
"""


def cluster_modules(final_entries: List[Dict]) -> Dict:
    if not final_entries:
        log_info("No final entries available; skipping module clustering.")
        return {'modules': []}
    router = ModelRouter()
    summary_text = '\n'.join(f"{item.get('filename')}: {item.get('high_level_summary', '')}" for item in final_entries)
    result = router.complete(f"{MODULE_PROMPT}\n{summary_text}", json_mode=True, model=CLUSTER_MODEL)
    output_text = result.get('output_text', '{"modules": []}')
    try:
        modules = json.loads(output_text)
    except json.JSONDecodeError:
        modules = {'modules': []}
    ensure_dir('app/db')
    with open(MODULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(modules, f, ensure_ascii=False, indent=2)
    log_info(f"Module clustering complete with {len(modules.get('modules', []))} modules")
    return modules
