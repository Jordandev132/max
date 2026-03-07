"""Max — Content Generator.

X-ONLY: generate_tweet(), generate_thread(), generate_news_commentary(),
generate_engagement_tweet(), humanize(). Uses shared LLM (local Qwen 35B).
Falls back to template-based generation if LLM unavailable.
"""
from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import datetime
from pathlib import Path

from . import config
from .identity import SYSTEM_PROMPT, HUMANIZE_PROMPT, BANNED_WORDS, VERBAL_TICS
from .content_bank import (
    TWEET_TEMPLATES, THREAD_HOOKS, HASHTAGS, CONTENT_IDEAS,
)

log = logging.getLogger("max.generator")

# ── Shared LLM ──
_llm_call = None
try:
    from llm_client import llm_call
    _llm_call = llm_call
except Exception:
    log.warning("Shared LLM not available — using template mode")


def _call_llm(prompt: str, max_tokens: int = 400, system: str | None = None) -> str | None:
    """Call shared LLM with Max's system prompt."""
    if not _llm_call:
        return None
    try:
        return _llm_call(
            system=system or SYSTEM_PROMPT,
            user=prompt,
            agent="max",
            task_type="writing",
            max_tokens=max_tokens,
        )
    except Exception as e:
        log.warning("LLM call failed: %s", e)
        return None


def _pick_hashtags(pillar: str, count: int = 2) -> list[str]:
    """Pick random niche hashtags for X. Max 2 per tweet (spec rule)."""
    pool = HASHTAGS.get(pillar, HASHTAGS.get("ai_automation", []))
    if not pool:
        return []
    return random.sample(pool, min(count, len(pool)))


def _get_atlas_context() -> str:
    """Pull latest AI/tech trends from Atlas knowledge base."""
    context_parts = []

    if config.ATLAS_TRENDS_FILE.exists():
        try:
            data = json.loads(config.ATLAS_TRENDS_FILE.read_text())
            findings = data.get("last_findings", [])
            if findings:
                context_parts.append("Recent Atlas findings:")
                for f in findings[:5]:
                    context_parts.append(f"- {f}")
        except Exception:
            pass

    if config.ATLAS_KB_DIR.exists():
        try:
            for f in sorted(config.ATLAS_KB_DIR.glob("*.json"))[-3:]:
                data = json.loads(f.read_text())
                if isinstance(data, dict):
                    summary = data.get("summary", "")
                    if summary and any(kw in summary.lower() for kw in [
                        "ai", "automation", "chatbot", "llm", "agent", "gpt", "claude",
                    ]):
                        context_parts.append(f"Atlas KB: {summary[:200]}")
        except Exception:
            pass

    return "\n".join(context_parts) if context_parts else ""


def _pick_pillar() -> str:
    """Pick a content pillar weighted by spec distribution."""
    pillars = list(config.PILLARS.keys())
    weights = [config.PILLARS[p]["weight"] for p in pillars]
    return random.choices(pillars, weights=weights, k=1)[0]


def _check_banned_words(text: str) -> str:
    """Remove banned AI-detection words from text."""
    result = text
    for word in BANNED_WORDS:
        if word.lower() in result.lower():
            result = result.replace(word, "")
            result = result.replace(word.title(), "")
            result = result.replace(word.upper(), "")
    # Clean up double spaces
    while "  " in result:
        result = result.replace("  ", " ")
    return result.strip()


def _load_recent_posts(days: int = 30) -> list[str]:
    """Load recent post content for dedup checking."""
    posts = []
    if config.HISTORY_FILE.exists():
        try:
            data = json.loads(config.HISTORY_FILE.read_text())
            for item in data[-100:]:
                posts.append(item.get("content", ""))
        except Exception:
            pass
    return posts


# ═══════════════════════════════════════════
#  Content Generation
# ═══════════════════════════════════════════

def generate_tweet(
    pillar: str | None = None,
    template_id: str | None = None,
    topic: str | None = None,
) -> dict:
    """Generate a single tweet using one of the 12 templates."""
    if not pillar:
        pillar = _pick_pillar()

    # Pick template
    if template_id and template_id in TWEET_TEMPLATES:
        template = TWEET_TEMPLATES[template_id]
    else:
        # Pick a template matching the pillar, or any template
        matching = [
            (tid, t) for tid, t in TWEET_TEMPLATES.items()
            if t["pillar"] == pillar
        ]
        if not matching:
            matching = list(TWEET_TEMPLATES.items())
        template_id, template = random.choice(matching)

    # Pick topic
    if not topic:
        ideas = CONTENT_IDEAS.get(pillar, CONTENT_IDEAS["ai_automation"])
        topic = random.choice(ideas)

    atlas_ctx = _get_atlas_context()
    prompt = template["prompt"].format(topic=topic)
    if atlas_ctx:
        prompt += f"\n\nTrending context from research:\n{atlas_ctx}"

    content = _call_llm(prompt, max_tokens=300)
    if not content:
        # Template fallback
        content = template["example"]

    content = _check_banned_words(content)
    # Trim to 280 chars
    if len(content) > 280:
        content = content[:277] + "..."

    hashtags = _pick_hashtags(pillar, 2)

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": "x",
        "pillar": pillar,
        "type": "tweet",
        "template": template_id,
        "topic": topic,
        "content": content,
        "hashtags": hashtags,
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
    }


def generate_thread(
    pillar: str | None = None,
    topic: str | None = None,
    tweet_count: int = 6,
) -> dict:
    """Generate a thread using spec's hook->context->stakes->value->takeaway->CTA."""
    if not pillar:
        pillar = _pick_pillar()
    if not topic:
        ideas = CONTENT_IDEAS.get(pillar, CONTENT_IDEAS["ai_automation"])
        topic = random.choice(ideas)

    tweet_count = min(tweet_count, config.MAX_THREAD_TWEETS)

    atlas_ctx = _get_atlas_context()
    prompt = f"""Write a Twitter/X thread ({tweet_count} tweets) about: {topic}

Pillar: {pillar}
{f'Context: {atlas_ctx}' if atlas_ctx else ''}

Thread structure:
1. HOOK — bold claim or curiosity gap (under 250 chars)
2. CONTEXT — why this matters NOW (under 250 chars)
3. STAKES — what you lose by not knowing this (under 250 chars)
4-{tweet_count - 2}. VALUE — actual insights, frameworks, tools (each under 250 chars)
{tweet_count - 1}. TAKEAWAY — one-liner people screenshot (under 250 chars)
{tweet_count}. CTA — invite follow/engagement, not desperate (under 250 chars)

Rules:
- Each tweet MUST be under 250 characters
- Number each tweet (1/, 2/, etc.)
- Use verbal tics naturally
- Include specific numbers and examples
- No hashtags in thread body
- Write in Max's voice: sharp, opinionated, practical

Return ONLY the numbered tweets, one per line."""

    content = _call_llm(prompt, max_tokens=800)

    if content:
        # Parse numbered tweets
        tweets = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # Remove numbering prefix (1/, 1., 1), etc.)
            import re
            cleaned = re.sub(r"^\d+[/.)\]]\s*", "", line)
            if cleaned:
                cleaned = _check_banned_words(cleaned)
                if len(cleaned) > 250:
                    cleaned = cleaned[:247] + "..."
                tweets.append(cleaned)
    else:
        # Template fallback
        hook = random.choice(THREAD_HOOKS)
        tweets = [
            hook.format(
                action="automated my entire content pipeline",
                timeframe="2 weeks", contrarian_take="AI won't replace you",
                cost="$50", time="40 hours", thing="12 AI agents",
                event="one of my agents crashed", topic=topic,
                common_belief="you need a team to scale",
                number="5", experience="building AI agents solo",
            ),
            f"Here's why this matters right now: {topic}",
            "Most people are sleeping on this. And it's costing them.",
            "The approach that actually works: keep it simple, ship fast, iterate.",
            f"Bottom line: {topic} is closer than you think.",
            "Follow me for more of this. I'm building this stuff daily.",
        ]

    hashtags = _pick_hashtags(pillar, 2)

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": "x",
        "pillar": pillar,
        "type": "thread",
        "topic": topic,
        "content": tweets,
        "hashtags": hashtags,
        "tweet_count": len(tweets),
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
    }


def generate_news_commentary(news_item: str) -> dict:
    """Generate rapid response to AI news from Atlas."""
    prompt = f"""Write rapid commentary on this AI news: {news_item}

Rules:
- Reference the news briefly (don't just repeat it)
- Give your HOT TAKE — what this actually means
- Explain what it means for builders/practitioners
- Use Max's voice: opinionated, practical, no hype
- Under 280 characters
- Start with a verbal tic if it fits naturally

Return ONLY the tweet text."""

    content = _call_llm(prompt, max_tokens=200)
    if not content:
        tic = random.choice(VERBAL_TICS)
        content = f"{tic} {news_item[:150]}. Most people are missing the real point here."

    content = _check_banned_words(content)
    if len(content) > 280:
        content = content[:277] + "..."

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": "x",
        "pillar": "ai_news",
        "type": "tweet",
        "template": "news_commentary",
        "topic": news_item,
        "content": content,
        "hashtags": _pick_hashtags("ai_news", 2),
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
    }


def generate_engagement_tweet(topic: str | None = None) -> dict:
    """Generate a question/poll tweet for engagement."""
    return generate_tweet(
        pillar="build_in_public",
        template_id="question_poll",
        topic=topic,
    )


def humanize(content: str) -> str:
    """Second LLM pass: personality injection, anti-AI-detection.

    Applies casual imperfections, sentence variation, tone randomization,
    dedup check vs recent posts.
    """
    # Check dedup against recent posts
    recent = _load_recent_posts(days=30)
    for post in recent:
        if post and content and _similarity(content, post) > 0.85:
            log.warning("Content too similar to recent post, adding variation")
            content = f"Real talk: {content}"

    prompt = f"""Humanize this tweet. Apply ALL rules from your instructions.

DRAFT:
{content}

Return ONLY the humanized version. No commentary."""

    result = _call_llm(prompt, max_tokens=300, system=HUMANIZE_PROMPT)
    if result:
        result = _check_banned_words(result)
        # Ensure char limit
        if len(result) > 280:
            result = result[:277] + "..."
        return result

    # Manual humanization fallback if LLM unavailable
    return _manual_humanize(content)


def _manual_humanize(text: str) -> str:
    """Manual humanization when LLM is unavailable."""
    text = _check_banned_words(text)

    # Add a verbal tic to ~30% of tweets
    if random.random() < 0.3 and not any(text.startswith(tic) for tic in VERBAL_TICS):
        tic = random.choice(VERBAL_TICS)
        text = f"{tic} {text[0].lower()}{text[1:]}" if text else text

    # Swap "because" -> "bc" occasionally
    if random.random() < 0.2:
        text = text.replace("because", "bc")
        text = text.replace("Because", "Bc")

    if len(text) > 280:
        text = text[:277] + "..."

    return text


def _similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity (0-1)."""
    if not a or not b:
        return 0.0
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def generate_batch(count: int = 4) -> list[dict]:
    """Generate a mixed batch of X content weighted by pillar.

    Default: 4 items per cycle. Mix of single tweets and occasional thread.
    Weighted by pillar distribution (40/25/25/10).
    """
    items = []

    for _ in range(count):
        pillar = _pick_pillar()

        # 20% chance of thread (roughly 1 per day with 4-5 posts/day)
        if random.random() < 0.15 and not any(i["type"] == "thread" for i in items):
            items.append(generate_thread(pillar=pillar))
        else:
            items.append(generate_tweet(pillar=pillar))

    log.info(
        "Generated batch: %d items (%s)",
        len(items),
        ", ".join(f"{i['type']}/{i['pillar']}" for i in items),
    )
    return items
