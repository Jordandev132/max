"""Max — Content Daemon.

Background loop:
- Every 4h: generate a batch of content (5 items)
- Every 30m: check Atlas feeds for trending topics
- Every 5m: heartbeat for Robotox
- Checks Claude Overseer directives for content requests

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
from .generator import generate_batch, generate_linkedin_post, generate_x_post
from .scheduler import add_batch, get_stats, prune_old

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
        "timestamp": datetime.now(config.ET).isoformat(),
    }, summary="Max daemon alive")


def _write_status(last_action: str, items_generated: int = 0):
    """Write status file for Robotox and dashboard."""
    stats = get_stats()
    status = {
        "agent": "max",
        "status": "running",
        "last_action": last_action,
        "last_update": datetime.now(config.ET).isoformat(),
        "items_generated_total": items_generated,
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
        # Check for content_directives aimed at max
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
                "agent", "startup", "saas", "bot",
            ]):
                topics.append(f)
    except Exception:
        pass
    return topics[:3]


def content_cycle(count: int = 5) -> dict:
    """Run one content generation cycle."""
    now = datetime.now(config.ET)
    log.info("=== Max Content Cycle %s ===", now.isoformat())

    total_generated = 0

    # 1. Check Claude directives
    directives = _check_overseer_directives()
    if directives:
        log.info("Found %d directives from Claude", len(directives))
        for d in directives[:3]:
            topic = d.get("topic", d.get("message", ""))
            platform = d.get("platform", "linkedin")
            if platform == "linkedin":
                item = generate_linkedin_post(topic=topic)
            elif platform == "x":
                item = generate_x_post(topic=topic)
            else:
                item = generate_linkedin_post(topic=topic)
            add_batch([item])
            total_generated += 1

    # 2. Check Atlas trends for timely content
    trends = _check_atlas_trends()
    if trends:
        log.info("Found %d AI trends from Atlas", len(trends))
        for trend in trends[:2]:
            item = generate_x_post(pillar="ai_tech", topic=trend)
            add_batch([item])
            total_generated += 1

    # 3. Generate regular batch
    remaining = max(1, count - total_generated)
    batch = generate_batch(count=remaining)
    add_batch(batch)
    total_generated += len(batch)

    # 4. Prune old items
    pruned = prune_old(days=30)

    # 5. Write status
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


def main():
    """Main daemon loop."""
    log.info("Max Content Agent starting — content_cycle=%ds, atlas_check=%ds",
             config.CONTENT_CYCLE_S, config.ATLAS_CHECK_S)

    _write_status("starting")

    last_content = 0
    last_atlas = 0
    last_heartbeat = 0
    total_generated = 0

    while _running:
        now = time.time()

        # Heartbeat
        if now - last_heartbeat >= config.HEARTBEAT_S:
            _heartbeat()
            last_heartbeat = now

        # Content generation cycle
        if now - last_content >= config.CONTENT_CYCLE_S:
            try:
                result = content_cycle()
                total_generated += result.get("generated", 0)
                _write_status(f"Generated {result.get('generated', 0)} items",
                              total_generated)
            except Exception as e:
                log.error("Content cycle failed: %s", e, exc_info=True)
                _write_status(f"Error: {e}")
            last_content = now

        # Atlas trend check (more frequent than full cycle)
        if now - last_atlas >= config.ATLAS_CHECK_S:
            trends = _check_atlas_trends()
            if trends:
                log.info("Atlas trends: %s", trends[:2])
            last_atlas = now

        time.sleep(30)

    log.info("Max daemon stopped. Total generated: %d", total_generated)
    _write_status("stopped", total_generated)
