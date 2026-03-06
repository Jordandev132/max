"""Max — Content Queue & Scheduler.

Manages content queue, schedules posts for optimal times,
tracks what's been posted and what's pending.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from . import config

log = logging.getLogger("max.scheduler")


def _load_queue() -> list[dict]:
    """Load content queue from disk."""
    if config.QUEUE_FILE.exists():
        try:
            return json.loads(config.QUEUE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_queue(queue: list[dict]) -> None:
    """Save content queue to disk."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.QUEUE_FILE.write_text(json.dumps(queue, indent=2))


def add_to_queue(item: dict) -> dict:
    """Add a generated content item to the posting queue."""
    queue = _load_queue()

    if "id" not in item:
        item["id"] = uuid.uuid4().hex[:12]
    if "queued_at" not in item:
        item["queued_at"] = datetime.now(config.ET).isoformat()
    if "status" not in item:
        item["status"] = "queued"

    # Auto-schedule if not scheduled
    if "scheduled_for" not in item:
        item["scheduled_for"] = _next_slot(item.get("platform", "x"))

    queue.append(item)
    _save_queue(queue)
    return item


def add_batch(items: list[dict]) -> int:
    """Add multiple items to queue."""
    queue = _load_queue()
    for item in items:
        if "id" not in item:
            item["id"] = uuid.uuid4().hex[:12]
        item["queued_at"] = datetime.now(config.ET).isoformat()
        item["status"] = "queued"
        if "scheduled_for" not in item:
            item["scheduled_for"] = _next_slot(item.get("platform", "x"))
        queue.append(item)
    _save_queue(queue)
    log.info("Added %d items to queue", len(items))
    return len(items)


def get_pending(platform: str | None = None) -> list[dict]:
    """Get pending (unposted) items, optionally filtered by platform."""
    queue = _load_queue()
    pending = [q for q in queue if q.get("status") in ("queued", "draft")]
    if platform:
        pending = [q for q in pending if q.get("platform") == platform]
    return pending


def mark_posted(item_id: str) -> bool:
    """Mark a queue item as posted."""
    queue = _load_queue()
    for item in queue:
        if item.get("id") == item_id:
            item["status"] = "posted"
            item["posted_at"] = datetime.now(config.ET).isoformat()
            _save_queue(queue)
            return True
    return False


def get_stats() -> dict:
    """Get queue statistics."""
    queue = _load_queue()
    now = datetime.now(config.ET)
    today = now.date().isoformat()

    stats = {
        "total": len(queue),
        "queued": sum(1 for q in queue if q.get("status") == "queued"),
        "draft": sum(1 for q in queue if q.get("status") == "draft"),
        "posted": sum(1 for q in queue if q.get("status") == "posted"),
        "posted_today": sum(
            1 for q in queue
            if q.get("status") == "posted"
            and q.get("posted_at", "").startswith(today)
        ),
        "by_platform": {},
    }

    for platform in config.PLATFORMS:
        platform_items = [q for q in queue if q.get("platform") == platform]
        stats["by_platform"][platform] = {
            "queued": sum(1 for q in platform_items if q.get("status") == "queued"),
            "posted": sum(1 for q in platform_items if q.get("status") == "posted"),
        }

    return stats


def _next_slot(platform: str) -> str:
    """Calculate next optimal posting slot for a platform.

    Optimal times (ET): 6-8 AM or 9-11 PM.
    Spaces posts at least 2 hours apart on same platform.
    """
    now = datetime.now(config.ET)
    queue = _load_queue()

    # Find latest scheduled time for this platform
    platform_times = []
    for q in queue:
        if q.get("platform") == platform and q.get("scheduled_for"):
            try:
                t = datetime.fromisoformat(q["scheduled_for"])
                platform_times.append(t)
            except (ValueError, TypeError):
                pass

    # Start from next optimal slot
    # Morning window: 6-8 AM, Evening window: 9-11 PM
    candidate = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    for _ in range(48):  # Look up to 48 hours ahead
        hour = candidate.hour
        is_optimal = (6 <= hour <= 8) or (21 <= hour <= 23)
        if is_optimal:
            # Check no conflict with existing posts (2h gap)
            conflict = any(
                abs((candidate - t).total_seconds()) < 7200
                for t in platform_times
            )
            if not conflict:
                return candidate.isoformat()
        candidate += timedelta(hours=1)

    # Fallback: just schedule 4 hours from now
    return (now + timedelta(hours=4)).isoformat()


def prune_old(days: int = 30) -> int:
    """Remove posted items older than N days."""
    queue = _load_queue()
    cutoff = (datetime.now(config.ET) - timedelta(days=days)).isoformat()
    original = len(queue)
    queue = [
        q for q in queue
        if q.get("status") != "posted" or q.get("posted_at", "") > cutoff
    ]
    pruned = original - len(queue)
    if pruned:
        _save_queue(queue)
        log.info("Pruned %d old items from queue", pruned)
    return pruned
