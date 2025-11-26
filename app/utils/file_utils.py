import json
import os
import pathlib
from typing import Optional


def safe_filename(name: str) -> str:
    return ''.join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip().replace(' ', '_')


def ensure_dir(path: str) -> None:
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def save_binary(content: bytes, destination: str) -> str:
    ensure_dir(os.path.dirname(destination))
    with open(destination, 'wb') as f:
        f.write(content)
    return destination


def load_text(path: str, default: str = '') -> str:
    if not os.path.exists(path):
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def append_jsonl(path: str, obj: dict) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def rewrite_jsonl(path: str, entries: list[dict]) -> None:
    """Rewrite an entire JSONL file with provided entries."""
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_json(path: str, obj: dict) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        entries = []
        for line in f:
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries


def list_files(folder: str) -> list[str]:
    if not folder or not os.path.exists(folder):
        return []
    paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            paths.append(os.path.join(root, file))
    return paths


def remove_file_if_exists(path: str) -> None:
    """Delete a file if present without raising when missing."""
    try:
        os.remove(path)
    except FileNotFoundError:
        return
