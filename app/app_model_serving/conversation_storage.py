"""
conversation_storage.py
========================
Persists conversation messages to JSON files on disk.

Layout:
  app/data/conversations/<uuid>/
    001.json   ← latest 25 messages (reverse chronological)
    002.json   ← next 25
    ...

Each JSON file: { "page": N, "messages": [ {query, results, created_at}, ... ] }
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

PAGE_SIZE = 25
MAX_MESSAGES = 1000

_BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "conversations"


def _conv_dir(conv_uuid: str) -> Path:
    return _BASE_DIR / conv_uuid


def _file_path(conv_uuid: str, page: int) -> Path:
    return _conv_dir(conv_uuid) / f"{page:03d}.json"


def rebuild_files(conv_uuid: str, messages: List[dict]) -> None:
    """
    Rebuild all JSON files for a conversation from a full message list.
    `messages` must be in reverse chronological order (newest first).
    Keeps only the latest MAX_MESSAGES.
    """
    msgs = messages[:MAX_MESSAGES]
    d = _conv_dir(conv_uuid)
    d.mkdir(parents=True, exist_ok=True)

    # remove old files
    for f in d.glob("*.json"):
        f.unlink()

    # write pages
    for i in range(0, len(msgs), PAGE_SIZE):
        page_num = (i // PAGE_SIZE) + 1
        chunk = msgs[i:i + PAGE_SIZE]
        payload = {"page": page_num, "messages": chunk}
        fp = _file_path(conv_uuid, page_num)
        fp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    logger.info("[ConvStorage] Rebuilt %d pages for conv %s (%d messages)",
                max(1, -(-len(msgs) // PAGE_SIZE)) if msgs else 0, conv_uuid, len(msgs))


def append_message(conv_uuid: str, message: dict, all_messages: List[dict]) -> None:
    """
    Append a new message and rebuild files.
    `all_messages` is the full list from DB in reverse chronological order.
    """
    rebuild_files(conv_uuid, all_messages)


def read_page(conv_uuid: str, page: int = 1) -> dict:
    """Read a specific page file. Returns {page, messages} or empty."""
    fp = _file_path(conv_uuid, page)
    if not fp.exists():
        return {"page": page, "messages": []}
    return json.loads(fp.read_text(encoding="utf-8"))


def total_pages(conv_uuid: str) -> int:
    """Count how many page files exist for a conversation."""
    d = _conv_dir(conv_uuid)
    if not d.exists():
        return 0
    return len(list(d.glob("*.json")))


def delete_files(conv_uuid: str) -> None:
    """Remove all files for a conversation."""
    d = _conv_dir(conv_uuid)
    if d.exists():
        for f in d.glob("*.json"):
            f.unlink()
        try:
            d.rmdir()
        except OSError:
            pass
