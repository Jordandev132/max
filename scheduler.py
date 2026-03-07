"""Max — Content Queue & Scheduler.

X-ONLY: manages content queue, schedules posts for optimal times,
tracks what's been posted and what's pending.
Optimal times from spec: 8:30 AM, 10:30 AM, 1:00 PM, 4:00 PM, 7:30 PM ET.
"""
from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import datetime, timedelta

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
        item["scheduled_for"] = _next_slot()

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
            item["scheduled_for"] = _next_slot()
        queue.append(item)
    _save_queue(queue)
    log.info("Added %d items to queue", len(items))
    return len(items)


def get_pending() -> list[dict]:
    """Get pending (unposted) items."""
    queue = _load_queue()
    return [q for q in queue if q.get("status") in ("queued", "draft")]


def get_due() -> list[dict]:
    """Get items that are due for posting (scheduled time has passed)."""
    now = datetime.now(config.ET)
    queue = _load_queue()
    due = []
    for q in queue:
        if q.get("status") != "queued":
            continue
        scheduled = q.get("scheduled_for")
        if not scheduled:
            continue
        try:
            sched_time = datetime.fromisoformat(scheduled)
            if sched_time <= now:
                due.append(q)
        except (ValueError, TypeError):
            pass
    return due


def mark_posted(item_id: str, post_result: dict | None = None) -> bool:
    """Mark a queue item as posted."""
    queue = _load_queue()
    for item in queue:
        if item.get("id") == item_id:
            item["status"] = "posted"
            item["posted_at"] = datetime.now(config.ET).isoformat()
            if post_result:
                item["post_result"] = {
                    k: v for k, v in post_result.items()
                    if k in ("tweet_id", "thread_id", "dry_run")
                }
            _save_queue(queue)
            return True
    return False


def get_stats() -> dict:
    """Get queue statistics — X only."""
    queue = _load_queue()
    now = datetime.now(config.ET)
    today = now.date().isoformat()

    return {
        "total": len(queue),
        "queued": sum(1 for q in queue if q.get("status") == "queued"),
        "draft": sum(1 for q in queue if q.get("status") == "draft"),
        "posted": sum(1 for q in queue if q.get("status") == "posted"),
        "posted_today": sum(
            1 for q in queue
            if q.get("status") == "posted"
            and q.get("posted_at", "").startswith(today)
        ),
        "dry_run_posted": sum(
            1 for q in queue
            if q.get("status") == "posted"
            and q.get("post_result", {}).get("dry_run")
        ),
    }


# ── Optimal posting slots (ET) from spec ──
_OPTIMAL_SLOTS = [
    (8, 30),   # 8:30 AM
    (10, 30),  # 10:30 AM
    (13, 0),   # 1:00 PM
    (16, 0),   # 4:00 PM
    (19, 30),  # 7:30 PM
]


def _next_slot() -> str:
    """Calculate next optimal posting slot for X.

    Uses spec's optimal times with +/-15min jitter.
    Ensures 2h minimum spacing between posts.
    Weekend: lighter schedule.
    """
    now = datetime.now(config.ET)
    queue = _load_queue()

    # Find all scheduled/posted times for today and tomorrow
    existing_times = []
    for q in queue:
        sched = q.get("scheduled_for")
        if sched:
            try:
                t = datetime.fromisoformat(sched)
                existing_times.append(t)
            except (ValueError, TypeError):
                pass

    # Weekend detection
    is_weekend = now.weekday() >= 5
    if is_weekend:
        # Only use 2-3 slots on weekends
        slots = _OPTIMAL_SLOTS[:2] if now.weekday() == 5 else _OPTIMAL_SLOTS[:1]
    else:
        slots = _OPTIMAL_SLOTS

    # Try each slot today and tomorrow
    for day_offset in range(3):  # Today, tomorrow, day after
        day = now + timedelta(days=day_offset)
        for hour, minute in slots:
            # Apply jitter: +/- 15 min
            jitter = random.randint(-config.TIMING_JITTER_M, config.TIMING_JITTER_M)
            candidate = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            candidate += timedelta(minutes=jitter)

            # Must be in the future
            if candidate <= now:
                continue

            # Check 2h spacing
            conflict = any(
                abs((candidate - t).total_seconds()) < config.MIN_POST_SPACING_S
                for t in existing_times
            )
            if not conflict:
                return candidate.isoformat()

    # Fallback: 4 hours from now
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
