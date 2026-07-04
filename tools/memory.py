"""Agent memory layer. Tracks what's been processed across runs so agents
don't repeat work and can detect changes over time.

Storage: simple JSON file at data/memory.json
"""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

MEMORY_PATH = Path("data/memory.json")


def _load() -> dict:
    if MEMORY_PATH.exists():
        return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    return {"processed": {}, "history": [], "run_count": 0}


def _save(mem: dict) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(mem, indent=2, default=str), encoding="utf-8")


def content_hash(text: str) -> str:
    """Short hash to detect if content changed."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def was_processed(key: str) -> bool:
    """Check if a given key (ad ID, influencer handle, video URL) was already processed."""
    mem = _load()
    return key in mem["processed"]


def mark_processed(key: str, metadata: dict | None = None) -> None:
    """Mark a key as processed with optional metadata."""
    mem = _load()
    mem["processed"][key] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(metadata or {}),
    }
    _save(mem)


def get_previous_value(key: str) -> dict | None:
    """Get the stored metadata for a previously processed key."""
    mem = _load()
    return mem["processed"].get(key)


def log_run(summary: str) -> None:
    """Log a pipeline run for historical tracking."""
    mem = _load()
    mem["run_count"] += 1
    mem["history"].append({
        "run": mem["run_count"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
    })
    # Keep last 20 runs
    mem["history"] = mem["history"][-20:]
    _save(mem)


def detect_changes(key: str, new_hash: str) -> str | None:
    """Compare current content hash with stored one. Returns old hash if changed, None if same."""
    mem = _load()
    prev = mem["processed"].get(key)
    if not prev:
        return None  # Never seen before
    old_hash = prev.get("content_hash")
    if old_hash and old_hash != new_hash:
        return old_hash
    return None


def get_run_history() -> list[dict]:
    """Get history of past runs."""
    mem = _load()
    return mem.get("history", [])


def get_stats() -> dict:
    """Get memory stats for status reporting."""
    mem = _load()
    return {
        "total_processed": len(mem["processed"]),
        "run_count": mem["run_count"],
        "last_run": mem["history"][-1]["timestamp"] if mem["history"] else "never",
    }
