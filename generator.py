"""Max — Content Generator.

Uses shared LLM (local Qwen 35B) to generate platform-specific content.
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
from .identity import SYSTEM_PROMPT, CHARACTER
from .content_bank import (
    HOOKS, HASHTAGS, LINKEDIN_TEMPLATES, X_THREAD_TEMPLATES,
    DEMO_CONCEPTS, CONTENT_IDEAS,
)

log = logging.getLogger("max.generator")

# ── Shared LLM ──
_llm_call = None
try:
    from llm_client import llm_call
    _llm_call = llm_call
except Exception:
    log.warning("Shared LLM not available — using template mode")


def _call_llm(prompt: str, max_tokens: int = 800) -> str | None:
    """Call shared LLM with Max's system prompt."""
    if not _llm_call:
        return None
    try:
        return _llm_call(
            system=SYSTEM_PROMPT,
            user=prompt,
            agent="max",
            task_type="writing",
            max_tokens=max_tokens,
        )
    except Exception as e:
        log.warning("LLM call failed: %s", e)
        return None


def _pick_hashtags(platform: str, pillar: str, count: int = 4) -> list[str]:
    """Pick random niche hashtags for platform+pillar."""
    pool = HASHTAGS.get(platform, {}).get(pillar, [])
    if not pool:
        return []
    return random.sample(pool, min(count, len(pool)))


def _get_atlas_context() -> str:
    """Pull latest AI/tech trends from Atlas knowledge base."""
    context_parts = []

    # Check Atlas background status for recent findings
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

    # Check Atlas KB for AI-related entries
    if config.ATLAS_KB_DIR.exists():
        try:
            for f in sorted(config.ATLAS_KB_DIR.glob("*.json"))[-3:]:
                data = json.loads(f.read_text())
                if isinstance(data, dict):
                    summary = data.get("summary", "")
                    if summary and any(kw in summary.lower() for kw in ["ai", "automation", "chatbot", "llm", "agent"]):
                        context_parts.append(f"Atlas KB: {summary[:200]}")
        except Exception:
            pass

    return "\n".join(context_parts) if context_parts else ""


# ═══════════════════════════════════════════
#  Content Generation
# ═══════════════════════════════════════════

def generate_linkedin_post(pillar: str = "ai_tech", topic: str | None = None) -> dict:
    """Generate a LinkedIn post optimized for agency leads."""
    template = random.choice(LINKEDIN_TEMPLATES)
    if not topic:
        ideas = CONTENT_IDEAS.get(pillar, CONTENT_IDEAS["ai_tech"])
        topic = random.choice(ideas)

    atlas_ctx = _get_atlas_context()
    prompt = f"""Write a LinkedIn post about: {topic}

Format: {template['format']}
Structure: {template['structure']}
Example hook style: {template['example_hook']}

{f'Trending context from research: {atlas_ctx}' if atlas_ctx else ''}

Rules:
- Professional but conversational — NOT corporate jargon
- Include concrete numbers (hours saved, cost, percentage)
- End with a clear CTA (DM me, check link in bio, etc.)
- 150-300 words
- No emojis in first line
- Make it feel like a real person sharing real results

Return ONLY the post text, no metadata."""

    content = _call_llm(prompt, max_tokens=600)
    if not content:
        # Template fallback
        content = f"""{template['example_hook']}

Here's what I learned building AI solutions for small businesses:

Most owners spend 15+ hours/week on tasks that a chatbot could handle in seconds.

I've been building these for clients — appointment booking, lead qualification, customer FAQ bots.

The results? An average of 12 hours/week saved and 3x faster response times.

If you run a small business and want to see what AI could automate for you — DM me "bot" and I'll show you."""

    hashtags = _pick_hashtags("linkedin", pillar, 3)

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": "linkedin",
        "pillar": pillar,
        "type": "post",
        "topic": topic,
        "content": content,
        "hashtags": hashtags,
        "template_used": template["format"],
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
    }


def generate_x_post(pillar: str = "build_in_public", topic: str | None = None) -> dict:
    """Generate an X (Twitter) post or thread starter."""
    if not topic:
        ideas = CONTENT_IDEAS.get(pillar, CONTENT_IDEAS["build_in_public"])
        topic = random.choice(ideas)

    atlas_ctx = _get_atlas_context()
    prompt = f"""Write a tweet about: {topic}

Pillar: {pillar}
{f'Context: {atlas_ctx}' if atlas_ctx else ''}

Rules:
- Max 280 characters for single tweet
- Punchy, direct, no fluff
- If build-in-public: include a specific metric or event
- If AI/tech: include a concrete example
- End with engagement hook (question or bold claim)
- No hashtags in the tweet body (added separately)

Return ONLY the tweet text."""

    content = _call_llm(prompt, max_tokens=200)
    if not content:
        hooks = HOOKS.get(pillar, HOOKS["ai_tech"])
        hook = random.choice(hooks)
        content = hook.format(
            action="qualifies leads", hours="15", task="customer support",
            time="3 hours", old_time="3 days", number="40",
            Business_type="Dental", result="3x more bookings",
            day=random.randint(1, 60), count=12, finding="a pricing bug",
            week=random.randint(1, 12), metric="lead response time",
            value="< 30 seconds", issue="a stale API key", month=1,
            system="content pipeline", bot_type="booking bot",
            business="dentist", price="500", savings="2,000",
        )

    hashtags = _pick_hashtags("x", pillar, 3)

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": "x",
        "pillar": pillar,
        "type": "tweet",
        "topic": topic,
        "content": content,
        "hashtags": hashtags,
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
    }


def generate_short_video_script(
    platform: str = "tiktok",
    pillar: str = "demo_sales",
    topic: str | None = None,
) -> dict:
    """Generate a script for TikTok/IG Reel/YouTube Short (7-30 seconds)."""
    if not topic:
        if pillar == "demo_sales":
            topic = random.choice(DEMO_CONCEPTS)
        else:
            ideas = CONTENT_IDEAS.get(pillar, CONTENT_IDEAS["ai_tech"])
            topic = random.choice(ideas)

    hooks = HOOKS.get(pillar, HOOKS["ai_tech"])
    hook = random.choice(hooks)

    prompt = f"""Write a short video script (15-25 seconds) about: {topic}

Platform: {platform}
Pillar: {pillar}
Hook style: {hook}

Structure:
- HOOK (0-3s): Bold text overlay + punchy voiceover
- BODY (3-20s): Show the demo/point with clear visuals
- CTA (20-25s): Clear next step

Rules:
- First 3 seconds MUST stop the scroll
- Show, don't tell — describe what's on screen
- Conversational, not scripted-sounding
- Include [TEXT OVERLAY] and [VOICEOVER] markers
- End with a specific CTA

Format:
[0-3s] HOOK
[TEXT OVERLAY]: ...
[VOICEOVER]: ...

[3-20s] BODY
[SCREEN]: ...
[VOICEOVER]: ...

[20-25s] CTA
[TEXT OVERLAY]: ...
[VOICEOVER]: ..."""

    content = _call_llm(prompt, max_tokens=500)
    if not content:
        content = f"""[0-3s] HOOK
[TEXT OVERLAY]: {hook}
[VOICEOVER]: {hook}

[3-15s] BODY
[SCREEN]: Screen recording of chatbot in action
[VOICEOVER]: I built this in under 3 hours. It handles bookings, FAQs, and follow-ups automatically.

[15-20s] CTA
[TEXT OVERLAY]: DM "bot" if you want one
[VOICEOVER]: I build these for small businesses. DM me if you want one."""

    hashtags = _pick_hashtags(platform, pillar, 4)

    return {
        "id": uuid.uuid4().hex[:12],
        "platform": platform,
        "pillar": pillar,
        "type": "video_script",
        "topic": topic,
        "content": content,
        "hashtags": hashtags,
        "generated_at": datetime.now(config.ET).isoformat(),
        "status": "draft",
        "duration_target": "15-25s",
    }


def generate_batch(count: int = 5) -> list[dict]:
    """Generate a mixed batch of content across platforms and pillars.

    Default mix weighted toward LinkedIn (agency leads) and X (build-in-public).
    """
    items = []

    # 1-2 LinkedIn posts (highest priority for leads)
    for _ in range(min(2, count)):
        pillar = random.choice(["ai_tech", "demo_sales", "ai_tech"])
        items.append(generate_linkedin_post(pillar=pillar))

    # 1-2 X posts
    remaining = count - len(items)
    for _ in range(min(2, remaining)):
        pillar = random.choice(["build_in_public", "ai_tech"])
        items.append(generate_x_post(pillar=pillar))

    # 1 video script
    remaining = count - len(items)
    if remaining > 0:
        platform = random.choice(["tiktok", "instagram", "youtube_shorts"])
        pillar = random.choice(["demo_sales", "ai_tech"])
        items.append(generate_short_video_script(platform=platform, pillar=pillar))

    log.info("Generated batch: %d items (%s)",
             len(items),
             ", ".join(f"{i['platform']}/{i['type']}" for i in items))
    return items
