"""Max — Content Templates & Bank.

12 tweet templates from spec, thread hooks, X-only hashtags,
and content ideas for each of the 4 pillars.
X-ONLY — no LinkedIn, TikTok, IG, YouTube Shorts.
"""

# ═══════════════════════════════════════════
#  12 TWEET TEMPLATES (from spec)
# ═══════════════════════════════════════════

TWEET_TEMPLATES = {
    # 1. "I Just Discovered" tweet
    "just_discovered": {
        "name": "I Just Discovered",
        "pillar": "ai_automation",
        "structure": "Discovery hook → What it does → Your take → Why it matters",
        "example": "Just found an AI tool that writes SQL from plain English. "
                   "Tested it on 3 client databases — it got every query right. "
                   "This changes everything for non-technical founders.",
        "prompt": "Write a 'just discovered' tweet about: {topic}. "
                  "Start with finding/discovery, explain what it does concretely, "
                  "add your hot take on why it matters. Under 280 chars.",
    },

    # 2. Contrarian Take
    "contrarian": {
        "name": "Contrarian Take",
        "pillar": "hot_takes",
        "structure": "Bold disagreement → Why most people are wrong → Your proof",
        "example": "Everyone says you need a team to build an AI product. "
                   "I'm running 12 autonomous agents solo. No employees. "
                   "The future isn't hiring more — it's building smarter.",
        "prompt": "Write a contrarian take tweet about: {topic}. "
                  "Start with a bold disagreement with conventional wisdom. "
                  "Back it up with something you've actually done. Under 280 chars.",
    },

    # 3. Build-in-Public Update
    "build_update": {
        "name": "Build-in-Public Update",
        "pillar": "build_in_public",
        "structure": "Day/week marker → What happened → Metric → What's next",
        "example": "Week 8 of running 12 AI agents: one found a pricing bug "
                   "that saved $47 on a trade. Another one crashed at 3 AM "
                   "and the health monitor auto-restarted it. This system is alive.",
        "prompt": "Write a build-in-public update tweet about: {topic}. "
                  "Include a specific number (revenue, clients, hours, agents). "
                  "Share what happened and what you learned. Under 280 chars.",
    },

    # 4. Data-Driven Insight
    "data_insight": {
        "name": "Data-Driven Insight",
        "pillar": "ai_news",
        "structure": "Surprising stat → Context → Your interpretation",
        "example": "73% of businesses that adopted AI chatbots saw ROI in under 90 days. "
                   "The ones that didn't? They tried to automate the wrong things first.",
        "prompt": "Write a data-driven insight tweet about: {topic}. "
                  "Lead with a specific number/stat (real or plausible), "
                  "then add your interpretation. Under 280 chars.",
    },

    # 5. Before/After
    "before_after": {
        "name": "Before/After",
        "pillar": "ai_automation",
        "structure": "Before state (painful) → After state (automated) → Result",
        "example": "Before: 4 hours/day answering the same 20 customer questions.\n"
                   "After: AI chatbot handles 80% automatically.\n"
                   "Result: Owner got their evenings back.",
        "prompt": "Write a before/after tweet about: {topic}. "
                  "Show the painful 'before' state, the automated 'after', "
                  "and the concrete result. Use line breaks. Under 280 chars.",
    },

    # 6. "Stop Doing This"
    "stop_doing": {
        "name": "Stop Doing This",
        "pillar": "hot_takes",
        "structure": "Bad practice call-out → Why it's wrong → What to do instead",
        "example": "Stop using ChatGPT with zero context and complaining "
                   "the output is generic. You're using a Ferrari in first gear. "
                   "Write a system prompt. Give it examples. The output changes completely.",
        "prompt": "Write a 'stop doing this' tweet about: {topic}. "
                  "Call out a common bad practice, explain why it fails, "
                  "and give the better approach. Under 280 chars.",
    },

    # 7. Tool Comparison
    "tool_comparison": {
        "name": "Tool Comparison",
        "pillar": "ai_automation",
        "structure": "Two tools → What each does best → Your verdict",
        "example": "Claude vs GPT-4 for coding: Claude writes cleaner code out of the box. "
                   "GPT-4 handles complex multi-file changes better. "
                   "I use both. Different tools, different jobs.",
        "prompt": "Write a tool comparison tweet about: {topic}. "
                  "Compare 2 AI tools/approaches honestly. Give your verdict. "
                  "No corporate-speak. Under 280 chars.",
    },

    # 8. Question/Poll
    "question_poll": {
        "name": "Question/Poll",
        "pillar": "build_in_public",
        "structure": "Context → Genuine question → Optional options",
        "example": "Running 12 AI agents and I need to pick: "
                   "add a 13th agent for content repurposing, or "
                   "make the existing 12 smarter? What would you prioritize?",
        "prompt": "Write a question/poll tweet about: {topic}. "
                  "Ask a genuine question your audience can answer. "
                  "Give context first. Under 280 chars.",
    },

    # 9. Rapid News Commentary
    "news_commentary": {
        "name": "Rapid News Commentary",
        "pillar": "ai_news",
        "structure": "News reference → Your instant take → What it means for builders",
        "example": "OpenAI just dropped GPT-5. Everyone's hype-posting. "
                   "Here's what actually matters: the tool-use API is 10x faster. "
                   "That's the real unlock for anyone building agents.",
        "prompt": "Write rapid commentary on this AI news: {topic}. "
                  "Reference the news, give your hot take, "
                  "explain what it means for builders. Under 280 chars.",
    },

    # 10. Tutorial Teaser
    "tutorial_teaser": {
        "name": "Tutorial Teaser",
        "pillar": "ai_automation",
        "structure": "Result preview → What you built → Teaser for full breakdown",
        "example": "Built an AI agent that monitors competitor prices 24/7. "
                   "Total cost: $0.12/day. No code beyond the initial setup. "
                   "Full breakdown thread coming this week.",
        "prompt": "Write a tutorial teaser tweet about: {topic}. "
                  "Show the result first, mention what you built, "
                  "tease a full breakdown. Under 280 chars.",
    },

    # 11. Vulnerability Post
    "vulnerability": {
        "name": "Vulnerability Post",
        "pillar": "build_in_public",
        "structure": "Honest admission → What went wrong → What you learned",
        "example": "Shipped an AI agent with a bug that burned $65 on bad trades. "
                   "My mistake: I assumed 'exit' meant 'exit all' when the user "
                   "meant one position. Lesson: never assume. Always confirm.",
        "prompt": "Write a vulnerability/honest-admission tweet about: {topic}. "
                  "Share a real mistake or struggle. What went wrong and "
                  "what you learned. No self-pity. Under 280 chars.",
    },

    # 12. Resource List
    "resource_list": {
        "name": "Resource List",
        "pillar": "ai_automation",
        "structure": "Listicle hook → 3-5 resources → Why each matters",
        "example": "5 AI tools I use every day that most people don't know about:\n"
                   "- Cursor (coding)\n- Perplexity (research)\n"
                   "- Claude (writing)\n- Whisper (transcription)\n"
                   "- n8n (automation)\nThread with details below.",
        "prompt": "Write a resource list tweet about: {topic}. "
                  "List 3-5 specific tools/resources with a hook. "
                  "Tease a thread. Under 280 chars.",
    },
}

# ═══════════════════════════════════════════
#  THREAD HOOK PATTERNS
# ═══════════════════════════════════════════

THREAD_HOOKS = [
    # Specific result hook
    "I {action} in {timeframe}. Here's exactly how (thread):",
    # Bold contrarian hook
    "Unpopular opinion: {contrarian_take}. Let me explain.",
    # Cost/investment hook
    "I spent {cost} and {time} building {thing}. Was it worth it? Here's the breakdown:",
    # Story hook
    "Last {timeframe}, {event}. It changed how I think about {topic}. Thread:",
    # Curiosity gap hook
    "Most people think {common_belief}. They're wrong. Here's why:",
    # Numbers hook
    "{number} things I learned from {experience}. Thread:",
]

# ═══════════════════════════════════════════
#  X-ONLY HASHTAGS (max 2 per tweet per spec)
# ═══════════════════════════════════════════

HASHTAGS = {
    "ai_automation": ["#AI", "#Automation", "#AIAgents", "#BuildWithAI", "#AITools"],
    "ai_news": ["#AINews", "#LLM", "#GPT", "#Claude", "#OpenAI", "#AIUpdate"],
    "build_in_public": ["#buildinpublic", "#indiehacker", "#shipfast", "#solofounder"],
    "hot_takes": ["#AI", "#HotTake", "#Tech", "#AIOpinions"],
}

# ═══════════════════════════════════════════
#  CONTENT IDEAS PER PILLAR
# ═══════════════════════════════════════════

CONTENT_IDEAS = {
    "ai_automation": [
        "AI tool that does X better than expected",
        "Automation I built that saves Y hours/week",
        "Why most people use AI tools wrong",
        "The $0/month AI stack that replaces 3 paid tools",
        "AI agent that monitors Z 24/7 for pennies",
        "How to build a custom AI workflow in under an hour",
        "The AI tool nobody talks about that I use daily",
        "Before/after: manual process vs AI-automated",
        "Building a chatbot that handles 80% of support tickets",
        "Why prompt engineering matters more than the model you pick",
    ],
    "ai_news": [
        "New model release and what it actually means for builders",
        "AI company acquisition and industry implications",
        "Benchmark results that matter vs benchmarks that don't",
        "AI regulation news and impact on indie builders",
        "Open-source model that rivals commercial ones",
        "AI pricing changes and what they signal",
        "New API feature that changes what's possible",
        "AI startup funding round and market trends",
    ],
    "build_in_public": [
        "Day X: what broke and how I fixed it",
        "Weekly agent performance report",
        "The hardest bug I've hit this week",
        "Revenue/metrics update — real numbers",
        "New agent added to the system — what it does",
        "Scaling challenge I didn't expect",
        "What running 12 AI agents actually costs",
        "The monitoring system that watches the watchers",
        "Lessons from automating my own workflow",
        "Open-sourcing part of the system — why and what",
    ],
    "hot_takes": [
        "Why most 'AI startups' are just API wrappers",
        "The AI tool everyone loves that I think is overrated",
        "Why learning to code still matters in the AI era",
        "The real reason AI projects fail (it's not the tech)",
        "Why I run everything on local models when possible",
        "The lie about AI replacing developers",
        "Why fine-tuning is overrated for most use cases",
        "The biggest waste of money in AI right now",
    ],
}
