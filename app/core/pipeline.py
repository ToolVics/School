from __future__ import annotations
import json
from typing import Dict, List
from app.config import RAW_KB_PATH, FINAL_KB_PATH
from app.core.extractor import extract_file
from app.core.supervisor import plan_for_file
from app.core.link_extractor import extract_links_content
from app.core.batch_processing.batch_manager import summarize_chunks
from app.core.refine import refine_entry
from app.core.module_clustering import cluster_modules
from app.utils.file_utils import append_jsonl, ensure_dir, list_files
from app.utils.log_utils import log_info


class Pipeline:
    def __init__(self, input_folder: str):
        self.input_folder = input_folder
        ensure_dir('app/db')

    def run(self) -> Dict[str, List[Dict]]:
        raw_entries: List[Dict] = []
        final_entries: List[Dict] = []
        files = list_files(self.input_folder)
        log_info(f"Pipeline discovered {len(files)} files")
        for path in files:
            text, links = extract_file(path)
            plan = plan_for_file(path, text[:400], len(links))
            link_summaries = extract_links_content(links, plan.get('max_links_to_follow', 0)) if plan.get('follow_links') else []
            raw_entry = summarize_chunks(path, text if plan.get('summarize_main', True) else '')
            raw_entry['links'] = link_summaries
            append_jsonl(RAW_KB_PATH, raw_entry)
            raw_entries.append(raw_entry)
            refined = refine_entry(path, raw_entry.get('raw_summary', ''), link_summaries)
            append_jsonl(FINAL_KB_PATH, refined)
            final_entries.append(refined)
        modules = cluster_modules(final_entries)
        return {'raw': raw_entries, 'final': final_entries, 'modules': modules}

    def reload_datastores(self) -> Dict[str, List[Dict]]:
        with open(RAW_KB_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            raw_entries = [json.loads(line) if line.strip().startswith('{') else eval(line) for line in f if line.strip()]
        with open(FINAL_KB_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            final_entries = [json.loads(line) if line.strip().startswith('{') else eval(line) for line in f if line.strip()]
        with open('app/db/modules.json', 'r', encoding='utf-8', errors='ignore') as f:
            modules = json.load(f) if f.read().strip() else {'modules': []}
        return {'raw': raw_entries, 'final': final_entries, 'modules': modules}
