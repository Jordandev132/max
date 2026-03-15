"""Max — Configuration.

X-ONLY content agent. Jordan's rule: no TikTok, IG, LinkedIn, YouTube Shorts.
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta, timezone
from pathlib import Path

ET = timezone(timedelta(hours=-5))

MAX_ROOT = Path(__file__).resolve().parent
DATA_DIR = MAX_ROOT / "data"

# ── Shared imports ──
sys.path.insert(0, str(Path.home() / "shared"))
sys.path.insert(0, str(Path.home()))

# ── Identity ──
AGENT_NAME = "Max"
ROLE = "AI Content Agent — X Only"

# ── Platform — X ONLY (Jordan's rule) ──
PLATFORMS = ["x"]

# ── Content Pillars (from spec — 4 pillars with weights) ──
PILLARS = {
    "ai_automation": {
        "name": "AI Automation",
        "weight": 0.40,
        "angle": "AI tools, workflows, automation demos, 'I built this' showcases",
    },
    "ai_news": {
        "name": "AI News & Trends",
        "weight": 0.25,
        "angle": "Breaking AI news, industry shifts, rapid commentary",
    },
    "build_in_public": {
        "name": "Build-in-Public",
        "weight": 0.25,
        "angle": "Day X updates on the 12-agent AI system, dev credibility, lessons learned",
    },
    "hot_takes": {
        "name": "Opinions & Hot Takes",
        "weight": 0.10,
        "angle": "Contrarian views, bold claims, strong opinions backed by experience",
    },
}

# ── Posting Schedule ──
POSTS_PER_DAY = 4                      # 4-5 posts/day (start conservative)
MIN_POST_SPACING_S = 7200              # 2h minimum between posts
TIMING_JITTER_M = 15                   # +/- 15 min randomization
OPTIMAL_HOURS_ET = [8, 10, 13, 16, 19] # EST slots from spec (8:30,10:30,1,4,7:30)
OPTIMAL_MINUTES = [0, 30]              # half-hour offsets

# Weekend schedule
WEEKEND_POSTS_SAT = 2                  # lighter Saturday
WEEKEND_POSTS_SUN = 0                  # skip Sunday

# ── Thread Settings ──
THREADS_PER_WEEK = 2
MAX_THREAD_TWEETS = 12
THREAD_DELAY_S = 2                     # seconds between thread tweets

# ── Auto-Reply Limits (safety) ──
MAX_REPLIES_PER_10MIN = 5
REPLY_DELAY_MIN_S = 180                # 3 min minimum before replying
REPLY_DELAY_MAX_S = 900                # 15 min maximum
REPLY_CHECK_INTERVAL_S = 900           # 15 min poll interval
REPLY_OWN_POSTS_PRIORITY = True        # Reply to own post comments first

# ── DRY_RUN — default TRUE until Jordan creates X account ──
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# ── X API Tier ──
X_API_TIER = os.getenv("X_API_TIER", "free")  # "free" or "basic"

# ── Cycle Intervals ──
CONTENT_CYCLE_S = 4 * 3600             # Generate content every 4 hours
POSTING_CHECK_S = 300                  # Check posting queue every 5 min
HEARTBEAT_S = 300                      # Heartbeat every 5 min
ATLAS_CHECK_S = 1800                   # Check Atlas feeds every 30 min

# ── File Paths ──
QUEUE_FILE = DATA_DIR / "content_queue.json"
STATUS_FILE = DATA_DIR / "max_status.json"
DRY_RUN_LOG = DATA_DIR / "dry_run_log.json"
HISTORY_FILE = DATA_DIR / "post_history.json"
OWN_POSTS_FILE = DATA_DIR / "own_posts.json"

# ── Atlas Integration ──
ATLAS_ENABLED = True
ATLAS_KB_DIR = Path.home() / "atlas" / "data" / "knowledge_base"
ATLAS_TRENDS_FILE = Path.home() / "atlas" / "data" / "background_status.json"

# ── Posting Jitter ──
POST_JITTER_MIN_S = 60                 # 1 min minimum jitter before posting
POST_JITTER_MAX_S = 300                # 5 min maximum jitter

# ── Claude Overseer ──
OVERSEER_DATA = Path.home() / "claude_overseer" / "data"

# ── Ensure data directory ──
DATA_DIR.mkdir(parents=True, exist_ok=True)
