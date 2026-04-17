"""Small JSON file cache helpers for expensive public-data requests."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


CACHE_DIR = Path("/tmp/host_public_cache")


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def load_json_cache(key: str, *, ttl_seconds: int) -> Any | None:
    path = _cache_path(key)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    created_at = float(payload.get("created_at", 0))
    if created_at <= 0 or (time.time() - created_at) > ttl_seconds:
        return None

    return payload.get("value")


def store_json_cache(key: str, value: Any) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(key)
        payload = {
            "created_at": time.time(),
            "value": value,
        }
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
    except OSError:
        return
