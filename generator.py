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
    ENGAGEMENT_BAIT, WEEKEND_TOPICS,
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
    if not config.ATLAS_ENABLED:
        return ""

    context_parts = []

    if config.ATLAS_TRENDS_FILE.exists():
        try:
            data = json.loads(config.ATLAS_TRENDS_FILE.read_text())
            findings = data.get("last_findings", [])
            if findings:
                context_parts.append("Recent Atlas findings:")
                for f in findings[:5]:
                    context_parts.append(f"- {f}")
                log.info("Atlas trends used: %s", findings[:3])
        except Exception as e:
            log.warning("Atlas trends file unreadable: %s", e)
    else:
        log.debug("Atlas trends file not found: %s", config.ATLAS_TRENDS_FILE)

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
                        log.info("Atlas KB used: %s — %s", f.name, summary[:80])
        except Exception as e:
            log.warning("Atlas KB read error: %s", e)
    else:
        log.debug("Atlas KB dir not found: %s", config.ATLAS_KB_DIR)

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


_recent_templates: list[str] = []  # track recent template IDs to avoid repeats


def _load_recent_posts(days: int = 30) -> list[str]:
    """Load recent post content for dedup checking (history + current queue)."""
    posts = []
    # From post history
    if config.HISTORY_FILE.exists():
        try:
            data = json.loads(config.HISTORY_FILE.read_text())
            for item in data[-100:]:
                posts.append(item.get("content", ""))
        except Exception:
            pass
    # From current queue too
    if config.QUEUE_FILE.exists():
        try:
            queue = json.loads(config.QUEUE_FILE.read_text())
            for item in queue:
                c = item.get("content", "")
                if isinstance(c, str):
                    posts.append(c)
                elif isinstance(c, list):
                    posts.extend(c)
        except Exception:
            pass
    return posts


def _is_duplicate(content: str, recent: list[str] | None = None) -> bool:
    """Check if content is too similar to recent posts/queue. Threshold 0.65."""
    if recent is None:
        recent = _load_recent_posts()
    for post in recent:
        if post and content and _similarity(content, post) > 0.65:
            return True
    return False


def _template_fallback(template: dict, topic: str, pillar: str) -> str:
    """Generate content from template when LLM is unavailable.

    Customizes with the topic, applies humanization, avoids repeats.
    """
    global _recent_templates

    # Build content from template structure + topic
    name = template.get("name", "")
    example = template.get("example", "")

    # Customize the example by injecting the topic
    tic = random.choice(VERBAL_TICS) if random.random() < 0.4 else ""
    prefix = f"{tic} " if tic else ""

    # Topic-aware generation based on template type
    tid = template.get("name", "").lower().replace(" ", "_")
    ideas = CONTENT_IDEAS.get(pillar, CONTENT_IDEAS["ai_automation"])
    alt_topic = random.choice(ideas) if ideas else topic

    # Use the topic to make it unique instead of returning static example
    if "discovered" in name.lower():
        content = f"{prefix}Just tested something for {topic}. The results surprised me. This is way more practical than people think."
    elif "contrarian" in name.lower():
        content = f"{prefix}Unpopular opinion: most people are wrong about {topic}. I've seen the data. Here's what actually works."
    elif "build" in name.lower() and "update" in name.lower():
        week = random.randint(4, 16)
        content = f"{prefix}Week {week} update: been working on {topic}. Shipped it. Already seeing results."
    elif "data" in name.lower():
        pct = random.randint(60, 95)
        content = f"{prefix}{pct}% of teams I've seen get {topic} wrong. The fix is simpler than you think."
    elif "before" in name.lower() and "after" in name.lower():
        content = f"Before: spending hours on {topic} manually.\nAfter: automated the whole thing.\nResult: got my time back."
    elif "stop" in name.lower():
        content = f"{prefix}Stop doing {topic} the hard way. I see this constantly. There's a better approach and it takes 10 minutes to set up."
    elif "comparison" in name.lower() or "tool" in name.lower():
        content = f"{prefix}Tested two different approaches to {topic}. One was 3x faster. The winner wasn't what I expected."
    elif "question" in name.lower() or "poll" in name.lower():
        content = f"Real question for anyone working on {topic}: what's been your biggest bottleneck? I'm leaning one direction but curious what you've seen."
    elif "tutorial" in name.lower():
        content = f"{prefix}Built something for {topic} that costs $0.10/day to run. Full breakdown coming this week."
    elif "vulnerability" in name.lower():
        content = f"{prefix}Honest moment: I messed up {topic} last week. Here's what went wrong and what I learned. Building in public means sharing this too."
    elif "resource" in name.lower():
        content = f"3 tools I use daily for {topic} that most people don't know about. Thread with details below."
    else:
        content = f"{prefix}{topic}. Most people are sleeping on this. And it's costing them."

    content = _manual_humanize(content)

    # Track to avoid consecutive same template
    _recent_templates.append(tid)
    if len(_recent_templates) > 5:
        _recent_templates.pop(0)

    return content


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
        # Template fallback — customize with topic, not raw example
        content = _template_fallback(template, topic, pillar)

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
    # Check dedup against recent posts + queue
    recent = _load_recent_posts(days=30)
    for post in recent:
        if post and content and _similarity(content, post) > 0.65:
            log.warning("Content too similar to recent post, adding variation")
            tic = random.choice(VERBAL_TICS)
            content = f"{tic} {content}"
            break

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


def generate_engagement_bait(topic: str | None = None) -> dict:
    """Generate an engagement bait tweet (comment X for Y, curiosity gap)."""
    from datetime import datetime
    templates = ENGAGEMENT_BAIT
    template = random.choice(templates)

    if not topic:
        ideas = CONTENT_IDEAS.get("ai_automation", [])
        topic = random.choice(ideas)

    content = template.format(topic=topic, keyword="AI", resource="my automation checklist")
    content = _manual_humanize(content)
    if len(content) > 280:
        content = content[:277] + "..."

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": "x",
        "pillar": "build_in_public",
        "type": "tweet",
        "template": "engagement_bait",
        "topic": topic,
        "content": content,
        "hashtags": _pick_hashtags("build_in_public", 1),
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
    }


def generate_weekend_tweet() -> dict:
    """Generate a lighter, more casual weekend tweet."""
    from datetime import datetime
    topic = random.choice(WEEKEND_TOPICS)
    tic = random.choice(VERBAL_TICS) if random.random() < 0.3 else ""
    prefix = f"{tic} " if tic else ""
    content = f"{prefix}{topic}"
    content = _manual_humanize(content)
    if len(content) > 280:
        content = content[:277] + "..."

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": "x",
        "pillar": "hot_takes",
        "type": "tweet",
        "template": "weekend_casual",
        "topic": topic,
        "content": content,
        "hashtags": [],
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
    }


def generate_batch(count: int = 4, is_weekend: bool = False) -> list[dict]:
    """Generate a mixed batch of X content weighted by pillar.

    Default: 4 items per cycle. Mix of single tweets and occasional thread.
    Weighted by pillar distribution (40/25/25/10).
    On weekends: mix in 1 casual post per batch.
    """
    items = []
    recent = _load_recent_posts()

    for i in range(count):
        pillar = _pick_pillar()

        # Weekend: first item is casual
        if is_weekend and i == 0:
            item = generate_weekend_tweet()
        # 15% chance of thread (roughly 1 per day with 4-5 posts/day)
        elif random.random() < 0.15 and not any(i["type"] == "thread" for i in items):
            item = generate_thread(pillar=pillar)
        # 10% chance of engagement bait
        elif random.random() < 0.10:
            item = generate_engagement_bait()
        else:
            item = generate_tweet(pillar=pillar)

        # Dedup check before adding
        content = item.get("content", "")
        if isinstance(content, str) and _is_duplicate(content, recent):
            log.info("Skipping duplicate content, regenerating")
            item = generate_tweet(pillar=pillar)  # try once more

        items.append(item)

    log.info(
        "Generated batch: %d items (%s)",
        len(items),
        ", ".join(f"{it['type']}/{it['pillar']}" for it in items),
    )
    return items
