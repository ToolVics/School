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
        f.write(f"{obj}\n")


def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [eval(line.strip()) for line in f if line.strip()]


def list_files(folder: str) -> list[str]:
    if not folder or not os.path.exists(folder):
        return []
    paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            paths.append(os.path.join(root, file))
    return paths
