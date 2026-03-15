"""Max — X Poster.

Posts tweets and threads to X via tweepy. Copied from Mercury XClient pattern.
DRY_RUN guard on EVERY post method.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from . import config

log = logging.getLogger("max.poster")

# Lazy import tweepy
_tweepy = None


def _get_tweepy():
    global _tweepy
    if _tweepy is None:
        try:
            import tweepy
            _tweepy = tweepy
        except ImportError:
            log.error("tweepy not installed — run: pip install tweepy")
    return _tweepy


class XPoster:
    """X (Twitter) posting client with DRY_RUN safety."""

    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv(config.MAX_ROOT / ".env")

        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self._client = None   # tweepy.Client (v2)
        self._api = None      # tweepy.API (v1.1)
        self._api_key = os.getenv("X_API_KEY", "")
        self._api_secret = os.getenv("X_API_SECRET", "")
        self._access_token = os.getenv("X_ACCESS_TOKEN", "")
        self._access_secret = os.getenv("X_ACCESS_TOKEN_SECRET", "")

        if self.dry_run:
            log.info("XPoster initialized in DRY_RUN mode — no live posting")
        else:
            log.info("XPoster initialized in LIVE mode")

    def _get_client(self):
        """Get tweepy v2 Client (for posting)."""
        tweepy = _get_tweepy()
        if not tweepy:
            return None
        if self._client is None:
            if not all([self._api_key, self._api_secret,
                        self._access_token, self._access_secret]):
                log.error("X API credentials missing — check .env")
                return None
            self._client = tweepy.Client(
                consumer_key=self._api_key,
                consumer_secret=self._api_secret,
                access_token=self._access_token,
                access_token_secret=self._access_secret,
                wait_on_rate_limit=True,
            )
        return self._client

    def _log_dry_run(self, action: str, data: dict) -> dict:
        """Log would-post content to dry_run_log.json with quality info."""
        from .identity import BANNED_WORDS

        text = data.get("text", "")
        # Check for banned words in content
        banned_found = [w for w in BANNED_WORDS if w.lower() in text.lower()]

        entry = {
            "timestamp": datetime.now(config.ET).isoformat(),
            "type": "thread" if action == "post_thread" else "tweet",
            "pillar": data.get("pillar", ""),
            "template": data.get("template", ""),
            "content": text if isinstance(text, str) else data.get("tweets", text),
            "hashtags": data.get("hashtags", []),
            "scheduled_for": data.get("scheduled_for", ""),
            "char_count": len(text) if isinstance(text, str) else sum(len(t) for t in (text if isinstance(text, list) else [])),
            "banned_words_found": banned_found,
            "humanized": True,
        }

        # Append to dry run log
        log_data = []
        if config.DRY_RUN_LOG.exists():
            try:
                log_data = json.loads(config.DRY_RUN_LOG.read_text())
            except Exception:
                pass
        log_data.append(entry)
        config.DRY_RUN_LOG.write_text(json.dumps(log_data, indent=2))

        log.info("[DRY_RUN] Would %s: %s", action, (text if isinstance(text, str) else str(text))[:80])
        return {"ok": True, "dry_run": True, **entry}

    def _track_own_post(self, tweet_id: str, content: str) -> None:
        """Track own posts for reply-to-own priority."""
        posts = []
        if config.OWN_POSTS_FILE.exists():
            try:
                posts = json.loads(config.OWN_POSTS_FILE.read_text())
            except Exception:
                pass
        posts.append({
            "tweet_id": tweet_id,
            "content": content[:100],
            "posted_at": datetime.now(config.ET).isoformat(),
        })
        # Keep last 100
        posts = posts[-100:]
        config.OWN_POSTS_FILE.write_text(json.dumps(posts, indent=2))

    def post_tweet(self, text: str, hashtags: list[str] | None = None,
                   cta_link: str | None = None) -> dict:
        """Post a single tweet. DRY_RUN safe.

        If cta_link is provided, posts main tweet WITHOUT the link,
        then auto-replies with the link (30-50% reach penalty avoidance).
        """
        # Append hashtags if provided
        if hashtags:
            tag_str = " ".join(hashtags[:2])  # Max 2 per spec
            if len(text) + len(tag_str) + 1 <= 280:
                text = f"{text}\n{tag_str}"

        if self.dry_run:
            data = {"text": text}
            if cta_link:
                data["cta_link_reply"] = cta_link
            return self._log_dry_run("post_tweet", data)

        client = self._get_client()
        if not client:
            return {"ok": False, "error": "No X API client available"}

        try:
            response = client.create_tweet(text=text)
            tweet_id = response.data["id"]
            log.info("Posted tweet %s: %s", tweet_id, text[:60])
            self._track_own_post(tweet_id, text)

            # Auto-reply with CTA link if provided
            if cta_link:
                self.reply_to(tweet_id, cta_link)
                log.info("Auto-replied CTA link to %s", tweet_id)

            return {
                "ok": True,
                "tweet_id": tweet_id,
                "text": text,
            }
        except Exception as e:
            log.error("Failed to post tweet: %s", e)
            return {"ok": False, "error": str(e)}

    def post_thread(self, tweets: list[str], hashtags: list[str] | None = None) -> dict:
        """Post a thread (chain of replies). DRY_RUN safe."""
        if self.dry_run:
            return self._log_dry_run("post_thread", {
                "tweets": tweets,
                "tweet_count": len(tweets),
                "text": tweets[0] if tweets else "",
            })

        client = self._get_client()
        if not client:
            return {"ok": False, "error": "No X API client available"}

        results = []
        prev_id = None

        for i, text in enumerate(tweets):
            # Add hashtags to last tweet only
            if i == len(tweets) - 1 and hashtags:
                tag_str = " ".join(hashtags[:2])
                if len(text) + len(tag_str) + 1 <= 250:
                    text = f"{text}\n{tag_str}"

            try:
                response = client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=prev_id,
                )
                tweet_id = response.data["id"]
                results.append({"ok": True, "tweet_id": tweet_id, "text": text})
                prev_id = tweet_id
                log.info("Thread %d/%d posted: %s", i + 1, len(tweets), tweet_id)
                if i == 0:
                    self._track_own_post(tweet_id, text)

                # Spec requirement: 2-sec delay between thread tweets
                if i < len(tweets) - 1:
                    time.sleep(config.THREAD_DELAY_S)

            except Exception as e:
                log.error("Thread tweet %d failed: %s", i + 1, e)
                results.append({"ok": False, "error": str(e)})
                break  # Stop if any tweet fails

        return {
            "ok": all(r.get("ok") for r in results),
            "thread_id": results[0].get("tweet_id") if results else None,
            "tweet_count": len(results),
            "results": results,
        }

    def reply_to(self, tweet_id: str, text: str) -> dict:
        """Post a reply to a specific tweet. DRY_RUN safe."""
        if self.dry_run:
            return self._log_dry_run("reply_to", {
                "reply_to_tweet_id": tweet_id,
                "text": text,
            })

        client = self._get_client()
        if not client:
            return {"ok": False, "error": "No X API client available"}

        try:
            response = client.create_tweet(
                text=text,
                in_reply_to_tweet_id=tweet_id,
            )
            reply_id = response.data["id"]
            log.info("Replied %s to %s: %s", reply_id, tweet_id, text[:60])
            return {"ok": True, "reply_id": reply_id, "text": text}
        except Exception as e:
            log.error("Reply failed: %s", e)
            return {"ok": False, "error": str(e)}

    def test_connection(self) -> dict:
        """Test X API credentials."""
        if self.dry_run:
            return {"ok": True, "dry_run": True, "message": "DRY_RUN mode — no live API test"}

        client = self._get_client()
        if not client:
            return {"ok": False, "error": "No X API client available"}

        try:
            me = client.get_me(user_fields=["public_metrics"])
            user = me.data
            return {
                "ok": True,
                "username": user.username,
                "name": user.name,
                "followers": user.public_metrics.get("followers_count", 0),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
