"""Max — Content Daemon.

X-ONLY background loop:
- Every 4h: content generation cycle (generate → humanize → queue)
- Every 5m: check posting queue for due items (post or dry-run log)
- Every 30m: check Atlas feeds for breaking AI news
- Every 15m: reply monitoring (DORMANT until API Basic)
- Every 5m: heartbeat for Robotox

Run: python -m max           (daemon loop)
     python -m max --once    (single cycle)
     python -m max --batch 5 (generate N items and exit)
"""
from __future__ import annotations

import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from . import config
from .generator import (
    generate_batch, generate_tweet, generate_thread,
    generate_news_commentary, humanize,
)
from .scheduler import add_batch, get_stats, get_due, mark_posted, prune_old
from .poster import XPoster
from .replier import AutoReplier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.DATA_DIR / "max.log"),
    ],
)
log = logging.getLogger("max")

_running = True


def _signal_handler(sig, frame):
    global _running
    log.info("Shutdown signal received")
    _running = False


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


def _publish_event(event_type: str, data: dict, summary: str = ""):
    """Publish to shared event bus."""
    try:
        from events import publish as bus_publish
        bus_publish(agent="max", event_type=event_type, data=data, summary=summary)
    except Exception:
        pass


def _heartbeat():
    """Publish heartbeat."""
    _publish_event("heartbeat", {
        "agent": "max",
        "status": "alive",
        "dry_run": config.DRY_RUN,
        "timestamp": datetime.now(config.ET).isoformat(),
    }, summary="Max daemon alive")


def _write_status(last_action: str, items_generated: int = 0,
                  posts_today: int = 0):
    """Write status file for Robotox, dashboard, and Shelby."""
    stats = get_stats()
    status = {
        "agent": "max",
        "status": "running",
        "mode": "DRY_RUN" if config.DRY_RUN else "LIVE",
        "last_action": last_action,
        "last_update": datetime.now(config.ET).isoformat(),
        "items_generated_total": items_generated,
        "posts_today": posts_today,
        "queue": stats,
    }
    config.STATUS_FILE.write_text(json.dumps(status, indent=2))


def _check_overseer_directives() -> list[dict]:
    """Check if Claude Overseer has content directives for Max."""
    directives = []
    directive_file = config.OVERSEER_DATA / "claude_status.json"
    if not directive_file.exists():
        return directives

    try:
        data = json.loads(directive_file.read_text())
        for d in data.get("content_directives", []):
            if d.get("agent") == "max" and d.get("status") != "done":
                directives.append(d)
    except Exception:
        pass
    return directives


def _check_atlas_trends() -> list[str]:
    """Pull trending AI topics from Atlas."""
    topics = []
    if not config.ATLAS_TRENDS_FILE.exists():
        return topics

    try:
        data = json.loads(config.ATLAS_TRENDS_FILE.read_text())
        findings = data.get("last_findings", [])
        for f in findings:
            if isinstance(f, str) and any(kw in f.lower() for kw in [
                "ai", "chatbot", "automation", "llm", "gpt", "claude",
                "agent", "startup", "saas", "bot", "openai", "anthropic",
            ]):
                topics.append(f)
    except Exception:
        pass
    return topics[:3]


def _is_weekend() -> bool:
    """Check if today is a weekend day."""
    return datetime.now(config.ET).weekday() >= 5  # Sat=5, Sun=6


def _posts_allowed_today() -> int:
    """How many posts are allowed today (lighter on weekends)."""
    day = datetime.now(config.ET).weekday()
    if day == 6:  # Sunday
        return config.WEEKEND_POSTS_SUN
    if day == 5:  # Saturday
        return config.WEEKEND_POSTS_SAT
    return config.POSTS_PER_DAY


def content_cycle(count: int = 4) -> dict:
    """Run one content generation cycle.

    1. Check Overseer directives
    2. Check Atlas trends → news commentary
    3. Generate batch (weighted by pillar)
    4. Humanize each item
    5. Add to queue with scheduled times
    """
    now = datetime.now(config.ET)
    log.info("=== Max Content Cycle %s ===", now.isoformat())

    total_generated = 0

    # 1. Check Claude directives
    directives = _check_overseer_directives()
    if directives:
        log.info("Found %d directives from Claude", len(directives))
        for d in directives[:3]:
            topic = d.get("topic", d.get("message", ""))
            pillar = d.get("pillar", "ai_automation")
            if d.get("type") == "thread":
                item = generate_thread(pillar=pillar, topic=topic)
            else:
                item = generate_tweet(pillar=pillar, topic=topic)
            # Humanize single tweets
            if item["type"] == "tweet":
                item["content"] = humanize(item["content"])
            elif item["type"] == "thread":
                item["content"] = [humanize(t) for t in item["content"]]
            add_batch([item])
            total_generated += 1

    # 2. Check Atlas trends for timely news commentary
    trends = _check_atlas_trends()
    if trends:
        log.info("Found %d AI trends from Atlas", len(trends))
        for trend in trends[:2]:
            item = generate_news_commentary(trend)
            item["content"] = humanize(item["content"])
            add_batch([item])
            total_generated += 1

    # 3. Generate regular batch (minus what we already generated)
    remaining = max(1, count - total_generated)
    batch = generate_batch(count=remaining)

    # 4. Humanize each item
    for item in batch:
        if item["type"] == "tweet":
            item["content"] = humanize(item["content"])
        elif item["type"] == "thread":
            item["content"] = [humanize(t) for t in item["content"]]

    # 5. Add to queue
    add_batch(batch)
    total_generated += len(batch)

    # Prune old items
    pruned = prune_old(days=30)

    # Write status
    _write_status(f"Generated {total_generated} items", total_generated)

    stats = get_stats()
    result = {
        "timestamp": now.isoformat(),
        "generated": total_generated,
        "from_directives": len(directives),
        "from_trends": len(trends),
        "pruned": pruned,
        "queue_stats": stats,
    }

    _publish_event("content_cycle", result,
                   summary=f"Max generated {total_generated} items")

    log.info("Cycle done: %d generated, queue=%d pending",
             total_generated, stats.get("queued", 0))
    return result


def _post_cycle(poster: XPoster) -> int:
    """Check queue for due items and post (or dry-run log)."""
    due_items = get_due()
    if not due_items:
        return 0

    posted = 0
    max_today = _posts_allowed_today()
    stats = get_stats()
    already_posted = stats.get("posted_today", 0)

    for item in due_items:
        if already_posted + posted >= max_today:
            log.info("Daily post limit reached (%d/%d)", already_posted + posted, max_today)
            break

        if item["type"] == "thread":
            tweets = item.get("content", [])
            if isinstance(tweets, list):
                result = poster.post_thread(tweets, hashtags=item.get("hashtags"))
            else:
                continue
        else:
            text = item.get("content", "")
            result = poster.post_tweet(text, hashtags=item.get("hashtags"))

        if result.get("ok"):
            mark_posted(item["id"], result)
            posted += 1

    if posted:
        log.info("Posted %d items (%s mode)", posted, "DRY_RUN" if poster.dry_run else "LIVE")
        _write_status(f"Posted {posted} items", posts_today=already_posted + posted)

    return posted


def main():
    """Main daemon loop."""
    log.info("Max Content Agent starting — mode=%s, cycle=%ds, post_check=%ds",
             "DRY_RUN" if config.DRY_RUN else "LIVE",
             config.CONTENT_CYCLE_S, config.POSTING_CHECK_S)

    poster = XPoster()
    replier = AutoReplier()

    _write_status("starting")

    last_content = 0
    last_post_check = 0
    last_atlas = 0
    last_heartbeat = 0
    last_reply_check = 0
    total_generated = 0
    total_posted = 0

    while _running:
        now = time.time()

        # Heartbeat (every 5 min)
        if now - last_heartbeat >= config.HEARTBEAT_S:
            _heartbeat()
            last_heartbeat = now

        # Content generation cycle (every 4h)
        if now - last_content >= config.CONTENT_CYCLE_S:
            try:
                result = content_cycle()
                total_generated += result.get("generated", 0)
                _write_status(
                    f"Generated {result.get('generated', 0)} items",
                    total_generated, total_posted,
                )
            except Exception as e:
                log.error("Content cycle failed: %s", e, exc_info=True)
                _write_status(f"Error: {e}")
            last_content = now

        # Post cycle (every 5 min) — check queue for due items
        if now - last_post_check >= config.POSTING_CHECK_S:
            try:
                posted = _post_cycle(poster)
                total_posted += posted
            except Exception as e:
                log.error("Post cycle failed: %s", e, exc_info=True)
            last_post_check = now

        # Atlas trend check (every 30 min)
        if now - last_atlas >= config.ATLAS_CHECK_S:
            trends = _check_atlas_trends()
            if trends:
                log.info("Atlas trends: %s", trends[:2])
            last_atlas = now

        # Reply monitoring (every 15 min — DORMANT until API Basic)
        if now - last_reply_check >= config.REPLY_CHECK_INTERVAL_S:
            try:
                result = replier.process_mentions(poster=poster)
                if result.get("status") == "dormant":
                    log.debug("Auto-reply dormant — needs API Basic tier")
            except Exception as e:
                log.error("Reply check failed: %s", e)
            last_reply_check = now

        time.sleep(30)

    log.info("Max daemon stopped. Generated: %d, Posted: %d", total_generated, total_posted)
    _write_status("stopped", total_generated, total_posted)
