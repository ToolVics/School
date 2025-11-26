from __future__ import annotations

import os
import json
from typing import Callable, Dict, List, Optional

from app.config import FINAL_KB_PATH, RAW_KB_PATH, MODULES_PATH
from app.core.batch_processing.batch_manager import summarize_chunks
from app.core.extractor import extract_file
from app.core.link_extractor import extract_links_content
from app.core.module_clustering import cluster_modules
from app.core.refine import refine_entry
from app.core.supervisor import plan_for_file
from app.utils.file_utils import append_jsonl, ensure_dir, list_files, remove_file_if_exists
from app.utils.log_utils import log_info


class Pipeline:
    def __init__(self, input_folder: str):
        self.input_folder = input_folder
        ensure_dir('app/db')
        self._ensure_api_key()

    @staticmethod
    def _ensure_api_key() -> None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Please add it to your environment or .env file before running the pipeline."
            )

    @staticmethod
    def _reset_datastores() -> None:
        remove_file_if_exists(RAW_KB_PATH)
        remove_file_if_exists(FINAL_KB_PATH)
        remove_file_if_exists(MODULES_PATH)
        ensure_dir('app/db')
        log_info("Cleared previous knowledge base outputs.")

    def run(
        self,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> Dict[str, List[Dict]]:
        raw_entries: List[Dict] = []
        final_entries: List[Dict] = []
        plan_entries: List[Dict] = []
        files = list_files(self.input_folder)
        log_info(f"Pipeline discovered {len(files)} files")
        if not files:
            log_info("No files found; skipping processing and returning empty results.")
            return {'raw': raw_entries, 'final': final_entries, 'modules': {'modules': []}, 'plans': plan_entries}
        self._reset_datastores()
        for idx, path in enumerate(files, start=1):
            if cancel_check and cancel_check():
                log_info("Pipeline cancellation requested; returning partial results.")
                break
            text, links = extract_file(path)
            if progress_callback:
                progress_callback("extract", idx, len(files))
            plan = plan_for_file(path, text[:400], len(links))
            plan_entries.append({"filename": path, **plan})
            if progress_callback:
                progress_callback("supervisor", idx, len(files))
            link_summaries = extract_links_content(links, plan.get('max_links_to_follow', 0)) if plan.get('follow_links') else []
            if progress_callback:
                progress_callback("links", idx, len(files))
            raw_entry = summarize_chunks(path, text if plan.get('summarize_main', True) else '')
            raw_entry['links'] = link_summaries
            raw_entry['plan'] = plan
            append_jsonl(RAW_KB_PATH, raw_entry)
            raw_entries.append(raw_entry)
            if progress_callback:
                progress_callback("batch", idx, len(files))
            if progress_callback:
                progress_callback("refine", idx, len(files))
            refined = refine_entry(path, raw_entry.get('raw_summary', ''), link_summaries)
            append_jsonl(FINAL_KB_PATH, refined)
            final_entries.append(refined)
        if final_entries and not (cancel_check and cancel_check()):
            if progress_callback:
                progress_callback("cluster", len(files), len(files))
            modules = cluster_modules(final_entries)
        else:
            modules = {'modules': []}
        return {'raw': raw_entries, 'final': final_entries, 'modules': modules, 'plans': plan_entries}

    def reload_datastores(self) -> Dict[str, List[Dict]]:
        def _safe_load_line(line: str) -> Dict:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                return {}

        try:
            with open(RAW_KB_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                raw_entries = [_safe_load_line(line) for line in f if line.strip()]
        except FileNotFoundError:
            raw_entries = []

        try:
            with open(FINAL_KB_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                final_entries = [_safe_load_line(line) for line in f if line.strip()]
        except FileNotFoundError:
            final_entries = []

        try:
            with open(MODULES_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                modules = json.loads(content) if content else {'modules': []}
        except FileNotFoundError:
            modules = {'modules': []}
        return {'raw': raw_entries, 'final': final_entries, 'modules': modules}
