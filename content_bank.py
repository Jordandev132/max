"""Max — Content Templates & Bank.

Hook templates, caption formats, hashtag sets, and content ideas
for AI/tech + build-in-public + demo-as-sales content.
"""

# ── Hook Templates (first 3 seconds) ──
HOOKS = {
    "ai_tech": [
        "I built a bot that {action} while I sleep",
        "This AI tool replaced {hours}h of manual work",
        "Your competitor is already using AI for {task}. Are you?",
        "I automated {task} in {time}. Here's how.",
        "Stop doing {task} manually. There's a better way.",
        "This chatbot books {number} appointments a day. No human needed.",
        "AI just did in {time} what used to take {old_time}",
        "{Business_type} owners: this bot handles your {task} 24/7",
        "I gave an AI agent one job. It did {result}.",
        "Most people don't know AI can do this yet.",
    ],
    "build_in_public": [
        "Day {day} of building a 12-agent AI system",
        "My AI agents just {action} while I was asleep",
        "This is what running {count} AI agents looks like",
        "One of my agents found {finding} today",
        "Building in public: here's what broke today",
        "Week {week} update: {metric} is now {value}",
        "The agent that watches the other agents just caught {issue}",
        "I let AI manage my entire {system}. Here's month {month}.",
    ],
    "demo_sales": [
        "Watch me build a {bot_type} for a {business} in {time}",
        "This {business} gets {result} from a bot I built them",
        "A {business} asked me to automate {task}. 48 hours later:",
        "Before vs after: {business} with an AI assistant",
        "I built this chatbot for ${price}. It saves them ${savings}/month.",
        "POV: you're a {business} and your new AI employee just started",
    ],
}

# ── Hashtag Sets (3-5 per post, niche only) ──
HASHTAGS = {
    "tiktok": {
        "ai_tech": ["#aiforbusiness", "#chatbotdemo", "#automationtools", "#aiagent", "#techstartup"],
        "build_in_public": ["#buildinpublic", "#indiedev", "#aiproject", "#devlog", "#techfounder"],
        "demo_sales": ["#smallbusinessai", "#chatbotbuilder", "#aiautomation", "#businessbot", "#leadgen"],
    },
    "instagram": {
        "ai_tech": ["#artificialintelligence", "#aiforbusiness", "#automationagency", "#chatbot"],
        "build_in_public": ["#buildinpublic", "#techfounder", "#aistartup", "#devlife"],
        "demo_sales": ["#chatbotdemo", "#smallbusinesstech", "#aiassistant", "#businessautomation"],
    },
    "x": {
        "ai_tech": ["#AI", "#LLM", "#Automation"],
        "build_in_public": ["#buildinpublic", "#indiehacker", "#shipfast"],
        "demo_sales": ["#chatbot", "#AIagency", "#smallbiz"],
    },
    "linkedin": {
        "ai_tech": ["#ArtificialIntelligence", "#Automation", "#SmallBusiness"],
        "build_in_public": ["#BuildInPublic", "#TechFounder", "#AI"],
        "demo_sales": ["#ChatbotDevelopment", "#BusinessAutomation", "#AIConsulting"],
    },
    "youtube_shorts": {
        "ai_tech": ["#AIDemo", "#Automation", "#Chatbot", "#Tech"],
        "build_in_public": ["#BuildInPublic", "#AIProject", "#DevLog"],
        "demo_sales": ["#ChatbotBuild", "#SmallBusinessAI", "#AIAgent"],
    },
}

# ── LinkedIn Post Templates ──
LINKEDIN_TEMPLATES = [
    {
        "format": "problem_solution",
        "structure": "Hook (problem) → What I built → Results (numbers) → CTA",
        "example_hook": "Most small businesses lose 15+ hours/week on tasks an AI could handle.",
    },
    {
        "format": "case_study",
        "structure": "Client type → Challenge → What I built → Results → Offer",
        "example_hook": "A dentist was losing $2K/month in missed appointments. I built them a bot.",
    },
    {
        "format": "build_in_public_update",
        "structure": "Update header → What happened → Lesson → What's next",
        "example_hook": "Week 4 of running 12 AI agents: one of them found a bug in another.",
    },
    {
        "format": "myth_buster",
        "structure": "Common myth → Why it's wrong → Proof → CTA",
        "example_hook": "'AI is only for big companies.' I built a chatbot for a local bakery for $200.",
    },
    {
        "format": "how_i_built",
        "structure": "What I built → Step-by-step (3 steps) → Results → DM if you want one",
        "example_hook": "I built an appointment booking bot in 3 hours. Here's exactly how.",
    },
]

# ── X Thread Templates ──
X_THREAD_TEMPLATES = [
    {
        "format": "build_log",
        "tweets": 5,
        "structure": ["Hook (what I built)", "Problem it solves", "How it works (technical but accessible)", "Results/metrics", "CTA (DM or follow)"],
    },
    {
        "format": "ai_tool_breakdown",
        "tweets": 4,
        "structure": ["This AI tool does X", "How I use it for Y", "Results", "Try it yourself / I build these"],
    },
    {
        "format": "daily_update",
        "tweets": 1,
        "structure": ["Day X update: what happened, what I learned, what's next"],
    },
]

# ── Demo Video Concepts ──
DEMO_CONCEPTS = [
    "Appointment booking chatbot for dentist/salon/gym",
    "Lead qualification bot for real estate agent",
    "FAQ bot for e-commerce store",
    "Customer support bot that handles 80% of questions",
    "Social media scheduling assistant",
    "Invoice and payment reminder bot",
    "Restaurant reservation bot with menu recommendations",
    "Fitness coach bot with workout plans",
    "Property listing bot for realtors",
    "Event registration and RSVP bot",
]

# ── Content Ideas Bank ──
CONTENT_IDEAS = {
    "ai_tech": [
        "5 tasks every small business should automate with AI",
        "I replaced my virtual assistant with a chatbot. Here's what happened.",
        "The AI stack I use to run a one-person agency",
        "Why most businesses fail at AI adoption (and how to avoid it)",
        "AI tools that actually save time vs AI tools that waste time",
        "How I use AI to deliver projects 3x faster",
        "The $200 chatbot that saves this business $2K/month",
        "AI isn't replacing jobs. It's replacing excuses.",
        "Your competitor hired an AI employee. Did you?",
        "The cheapest AI tools that give the most ROI for small business",
    ],
    "build_in_public": [
        "Day X: one agent broke another agent. Here's what I learned.",
        "My AI system processed X tasks while I slept",
        "The hardest part of building an AI system nobody talks about",
        "Revenue update: month X of the AI agency",
        "How I monitor 12 AI agents from one dashboard",
        "The agent that watches all other agents (Robotox deep dive)",
        "What happens when an AI agent makes a mistake",
        "Building an AI agency from scratch — no funding, no team",
        "The real cost of running 12 AI agents (spoiler: less than you think)",
        "Why I build everything with Python and LLMs",
    ],
    "demo_sales": [
        "Building a chatbot for a local {business} LIVE",
        "This bot answers 50 questions a day so the owner doesn't have to",
        "Before/after: manual booking vs AI booking",
        "Client spotlight: how {business} saved X hours with a bot",
        "The 3-step process I use to build any chatbot",
        "Why every dentist/salon/gym needs a booking bot in 2026",
        "I cold-DMed this to 10 businesses. 4 said yes.",
        "Free chatbot challenge: building 3 bots for local businesses",
        "What a $500 chatbot actually does for a small business",
        "The exact DM I send to get chatbot clients",
    ],
}
