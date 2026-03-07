"""Max — Auto-Reply System.

Monitors mentions and replies to Max's tweets, generates contextual
replies using Max's voice. Rate-limited for safety.

STATUS: SCAFFOLDED BUT DORMANT
The X Free API tier has very limited read access (no search, no mentions
endpoint). This module will be dormant until Jordan approves X API Basic
tier ($200/mo). It logs a clear message and returns gracefully.
"""
from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path

from . import config
from .identity import SYSTEM_PROMPT

log = logging.getLogger("max.replier")

# ── Shared LLM ──
_llm_call = None
try:
    from llm_client import llm_call
    _llm_call = llm_call
except Exception:
    pass


class AutoReplier:
    """Auto-reply system for X mentions. DORMANT until API Basic tier."""

    def __init__(self):
        self._last_mention_id: str | None = None
        self._reply_count_window: list[float] = []  # timestamps of recent replies
        self._state_file = config.DATA_DIR / "replier_state.json"
        self._load_state()

    def _load_state(self):
        """Load last processed mention ID."""
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                self._last_mention_id = data.get("last_mention_id")
            except Exception:
                pass

    def _save_state(self):
        """Save replier state."""
        data = {
            "last_mention_id": self._last_mention_id,
            "last_updated": datetime.now(config.ET).isoformat(),
        }
        self._state_file.write_text(json.dumps(data, indent=2))

    def is_available(self) -> bool:
        """Check if auto-reply is available (needs API Basic tier)."""
        return config.X_API_TIER == "basic"

    def check_mentions(self) -> list[dict]:
        """Poll X API for mentions/replies.

        FREE tier: no mentions endpoint available.
        Returns empty list and logs dormant message.
        """
        if not self.is_available():
            log.debug(
                "Auto-reply DORMANT — requires X API Basic tier ($200/mo). "
                "Current tier: %s", config.X_API_TIER,
            )
            return []

        # When API Basic is available, this will use:
        # client.get_users_mentions(id=user_id, since_id=self._last_mention_id)
        log.info("Checking mentions (API Basic tier)")
        return []

    def _is_rate_ok(self) -> bool:
        """Check if we're within rate limits (5 replies per 10 min)."""
        now = time.time()
        # Remove entries older than 10 minutes
        self._reply_count_window = [
            t for t in self._reply_count_window if now - t < 600
        ]
        return len(self._reply_count_window) < config.MAX_REPLIES_PER_10MIN

    def _get_reply_delay(self) -> int:
        """Random delay before replying (3-15 min). Mimics human behavior."""
        return random.randint(config.REPLY_DELAY_MIN_S, config.REPLY_DELAY_MAX_S)

    def generate_reply(self, mention: dict) -> str | None:
        """Generate a contextual reply using Max's voice.

        Args:
            mention: dict with 'text', 'author_username', 'id' fields.

        Returns:
            Reply text or None if generation fails.
        """
        if not _llm_call:
            return None

        author = mention.get("author_username", "someone")
        original_text = mention.get("text", "")

        prompt = f"""Someone replied to your tweet or mentioned you. Generate a reply.

Their message: "{original_text}"
Their username: @{author}

Rules:
- Reply in Max's voice: sharp, knowledgeable, helpful
- Reference something SPECIFIC from their message (proves you read it)
- If they asked a question, answer it concisely
- If they disagreed, engage thoughtfully (not defensively)
- Mix in a question sometimes: "Have you tried X?" or "What's your setup?"
- Keep under 280 characters
- Don't start with "Great question!" or similar AI cliches
- Don't use @mentions — X adds those automatically

Return ONLY the reply text."""

        try:
            reply = _llm_call(
                system=SYSTEM_PROMPT,
                user=prompt,
                agent="max",
                task_type="writing",
                max_tokens=200,
            )
            return reply
        except Exception as e:
            log.warning("Reply generation failed: %s", e)
            return None

    def process_mentions(self, poster=None) -> dict:
        """Process pending mentions and generate replies.

        Args:
            poster: XPoster instance for posting replies.

        Returns:
            Summary dict with counts.
        """
        if not self.is_available():
            return {
                "status": "dormant",
                "reason": "Requires X API Basic tier",
                "tier": config.X_API_TIER,
            }

        mentions = self.check_mentions()
        if not mentions:
            return {"status": "ok", "mentions_found": 0, "replies_sent": 0}

        replies_sent = 0

        for mention in mentions:
            if not self._is_rate_ok():
                log.warning("Reply rate limit reached — pausing")
                break

            reply_text = self.generate_reply(mention)
            if not reply_text:
                continue

            # Delay before replying (human behavior)
            delay = self._get_reply_delay()
            log.info("Delaying %ds before replying to %s", delay, mention.get("id"))
            time.sleep(delay)

            if poster:
                result = poster.reply_to(mention["id"], reply_text)
                if result.get("ok"):
                    replies_sent += 1
                    self._reply_count_window.append(time.time())
                    self._last_mention_id = mention["id"]

        self._save_state()

        return {
            "status": "ok",
            "mentions_found": len(mentions),
            "replies_sent": replies_sent,
        }
