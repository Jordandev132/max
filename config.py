"""Max — Configuration."""
from __future__ import annotations

import os
import sys
from datetime import timedelta, timezone
from pathlib import Path

ET = timezone(timedelta(hours=-5))

MAX_ROOT = Path(__file__).resolve().parent
DATA_DIR = MAX_ROOT / "data"

# ── Shared LLM ──
sys.path.insert(0, str(Path.home() / "shared"))
sys.path.insert(0, str(Path.home()))

# ── Identity ──
AGENT_NAME = "Max"
ROLE = "AI Content Agent"
BRAND_HANDLE = "@abdalla.dev"  # Jordan can update

# ── Platforms ──
PLATFORMS = ["tiktok", "instagram", "x", "linkedin", "youtube_shorts"]

# ── Content Pillars ──
PILLARS = {
    "ai_tech": {
        "name": "AI / Tech",
        "angle": "AI can do this — automation demos, chatbot showcases, AI for business",
        "platforms": ["tiktok", "instagram", "x", "linkedin", "youtube_shorts"],
    },
    "build_in_public": {
        "name": "Build-in-Public",
        "angle": "Day X of building a 12-agent AI system — dev credibility, potential leads",
        "platforms": ["x", "linkedin"],
    },
    "demo_sales": {
        "name": "Demo-as-Sales-Tool",
        "angle": "Watch me build a chatbot for [business] — cold DM collateral",
        "platforms": ["tiktok", "instagram", "linkedin", "youtube_shorts"],
    },
}

# ── Weekly Targets (from plan) ──
WEEKLY_TARGETS = {
    "tiktok": 3,       # 2-3 AI/tech reels
    "instagram": 2,    # 1-2 reels
    "x": 5,            # 3-5 posts (incl. build-in-public)
    "linkedin": 4,     # 3-5 posts (CRITICAL for agency leads)
    "youtube_shorts": 2,  # 1-2 repurposed
}

# ── Content Rules ──
CONTENT_RULES = [
    "First 3 seconds MUST hook — bold text overlay or punchy opening line",
    "7-30 second reels for TikTok/IG/YouTube Shorts",
    "3-5 NICHE hashtags only — NEVER #foryou #viral #fyp",
    "Each platform gets UNIQUE content — no cross-posting with watermarks",
    "Optimal posting: 6-8 AM ET or 9-11 PM ET",
    "LinkedIn posts: professional but conversational, concrete numbers",
    "X posts: punchy, thread-friendly, build-in-public angle",
    "Demo videos: show the build process, end with CTA",
    "Always include a CTA — DM me, link in bio, follow for more",
]

# ── Cycle Intervals ──
CONTENT_CYCLE_S = 4 * 3600   # Generate content every 4 hours
HEARTBEAT_S = 300             # Heartbeat every 5 min
ATLAS_CHECK_S = 1800          # Check Atlas feeds every 30 min

# ── File Paths ──
QUEUE_FILE = DATA_DIR / "content_queue.json"
STATUS_FILE = DATA_DIR / "max_status.json"
IDEAS_FILE = DATA_DIR / "ideas.json"
CALENDAR_FILE = DATA_DIR / "content_calendar.json"
METRICS_FILE = DATA_DIR / "metrics.json"

# ── Atlas Integration ──
ATLAS_KB_DIR = Path.home() / "atlas" / "data" / "knowledge_base"
ATLAS_TRENDS_FILE = Path.home() / "atlas" / "data" / "background_status.json"

# ── Claude Overseer ──
OVERSEER_DATA = Path.home() / "claude_overseer" / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
