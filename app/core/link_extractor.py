from __future__ import annotations
import os
import re
import requests
from typing import List, Dict

from app.utils.file_utils import ensure_dir, save_binary
from app.extractors.extract_text import extract_text_generic
from app.utils.log_utils import log_info, log_error
from app.config import DOWNLOADS_DIR, LINK_MODEL
from app.models.model_router import ModelRouter

SAFE_EXTENSIONS = {'.pdf', '.html', '.htm', '.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
MAX_ATTEMPTS = 1


def _download_file(url: str) -> str:
    ensure_dir(DOWNLOADS_DIR)
    for _ in range(MAX_ATTEMPTS):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            filename = os.path.join(DOWNLOADS_DIR, os.path.basename(url.split('?')[0]))
            ext = os.path.splitext(filename)[1].lower()
            if ext and ext not in SAFE_EXTENSIONS:
                raise ValueError('Unsafe extension')
            save_binary(response.content, filename)
            return filename
        except Exception as exc:  # noqa: BLE001
            log_error(f"Download failed for {url}: {exc}")
            break
    return ''


def _infer_from_url(url: str) -> str:
    router = ModelRouter()
    prompt = f"The URL {url} could not be downloaded. Infer likely page content in 5 sentences."
    result = router.complete(prompt, model=LINK_MODEL)
    return result.get('output_text', '')


def _process_youtube(url: str) -> str:
    router = ModelRouter()
    prompt = f"Infer transcript highlights for YouTube video {url} in 5 bullet points."
    result = router.complete(prompt, model=LINK_MODEL)
    return result.get('output_text', '')


def _link_priority(url: str) -> int:
    lower = url.lower()
    skip_terms = ["login", "signin", "brightspace", "logout", "account"]
    if any(term in lower for term in skip_terms):
        return -1
    score = 0
    if 'doi.org' in lower:
        score += 100
    if any(media in lower for media in ['youtube.com', 'youtu.be', 'vimeo.com']):
        score += 80
    if any(keyword in lower for keyword in ['reading', 'chapter', 'pdf', 'appendix']):
        score += 60
    if any(struct in lower for struct in ['reference', 'citation', 'footnote']):
        score += 40
    return score


def extract_links_content(links: List[str], max_links: int = 3) -> List[Dict[str, str]]:
    collected: List[Dict[str, str]] = []
    ranked_links = sorted(links, key=_link_priority, reverse=True)
    for url in ranked_links:
        if len(collected) >= max_links:
            break
        priority = _link_priority(url)
        if priority < 0:
            log_info(f"Skipping navigation or login link: {url}")
            continue
        if 'youtube.com' in url or 'youtu.be' in url or 'vimeo.com' in url:
            content = _process_youtube(url)
            collected.append({'url': url, 'content': content})
            continue
        if re.match(r'^https?://', url):
            downloaded = _download_file(url)
            if downloaded:
                try:
                    text, _ = extract_text_generic(downloaded)
                    if text.strip():
                        collected.append({'url': url, 'content': text})
                    else:
                        collected.append({'url': url, 'content': _infer_from_url(url)})
                except Exception as exc:  # noqa: BLE001
                    log_error(f"Skipping invalid link {url}: {exc}")
                    continue
            else:
                try:
                    inferred = _infer_from_url(url)
                    if inferred.strip():
                        collected.append({'url': url, 'content': inferred})
                except Exception as exc:  # noqa: BLE001
                    log_error(f"Skipping invalid link {url}: {exc}")
                    continue
    log_info(f"Link extraction completed: {len(collected)} links processed")
    return collected
