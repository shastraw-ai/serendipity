"""The catalog of Skills. Add a Skill = add an entry here (no orchestration code)."""
from __future__ import annotations

import random

from .base import Skill

EMAIL_DIGEST = Skill(
    name="email_digest",
    title="Email Digest",
    description="Summarize your most recent important emails and suggest what to act on.",
    system_prompt=(
        "You are a helpful assistant that triages the user's Gmail. Fetch recent emails, "
        "identify what actually matters (skip newsletters/promotions unless notable), and "
        "summarize the important ones."
    ),
    allowed_tools=["list_emails", "list_calendar_events"],
    seed_instruction="Give me a digest of my important recent emails and what I should act on.",
)

NEWS_FOR_YOU = Skill(
    name="news_for_you",
    title="News For You",
    description="A deep dive into one story from one of your interests.",
    system_prompt=(
        "You are a personal news curator doing a single deep dive — not a broad roundup. "
        "You are given ONE of the user's interests. Search the web for the latest news on it "
        "and look at the top ~3 results, then pick the single most interesting or important "
        "story. Go one level deeper on that ONE story: read the source article with fetch_url "
        "(or run a follow-up search for background/reactions) to get detail beyond the "
        "snippet. Then write a focused, substantive summary of that one story — what "
        "happened, the key specifics, and why it matters — and link the source."
    ),
    allowed_tools=["web_search", "fetch_url"],
    seed_instruction="Pick one story from my interest and give me the deep dive.",
    uses_interests=True,
    sample_one_interest=True,
)

TODAYS_PLAN = Skill(
    name="todays_plan",
    title="Today's Plan",
    description="Summarize today's calendar and suggest how to focus the day.",
    system_prompt=(
        "You are a scheduling assistant. Fetch today's Google Calendar events (use the "
        "current datetime to build the day's start/end window), summarize the day in order, "
        "flag conflicts or tight gaps, and suggest how to focus.\n\n"
        "If the current time is late in the day (roughly 6pm local or later) and today has no "
        "more events remaining, also fetch tomorrow's calendar events and add a short 'Looking "
        "ahead to tomorrow' section summarizing that day, so the user can start planning ahead. "
        "Skip this extra section if it's earlier in the day or today still has events left."
    ),
    allowed_tools=["list_calendar_events", "list_emails"],
    seed_instruction="What does my day look like, and how should I plan around it?",
)

LATEST_PAPERS = Skill(
    name="latest_papers",
    title="Latest Papers",
    description="A few genuinely interesting recent research papers, explained.",
    system_prompt=(
        "You are a research scout. Search the web for recent (last few days to weeks) "
        "notable papers or preprints across science and tech — not tied to any particular "
        "topic. Prefer arXiv, official conference/journal pages, or credible tech press "
        "covering a paper. Pick 2-3 that are genuinely interesting or significant (novel "
        "result, notable authors/lab, real-world impact) rather than just the first hits. "
        "For each, read enough (fetch_url on the abstract or announcement page if useful) "
        "to explain in plain language what it does and why it matters."
    ),
    allowed_tools=["web_search", "fetch_url"],
    seed_instruction="What are some interesting recent papers I should know about?",
)

LATEST_FUNDED_STARTUPS = Skill(
    name="latest_funded_startups",
    title="Latest Funded Startups",
    description="Recently announced startup funding rounds worth knowing about.",
    system_prompt=(
        "You are a startup and venture news scout. Search the web for startup funding "
        "announcements from the last few days (seed through later rounds), across any "
        "industry. Pick 3-4 that are genuinely notable (large round, notable investors, "
        "interesting product or market) rather than just the first hits. For each, note the "
        "company, what it does, the round size and stage, and lead investors if reported."
    ),
    allowed_tools=["web_search", "fetch_url"],
    seed_instruction=(
        "What startup funding rounds have been announced recently that are worth knowing about?"
    ),
)

SCHEDULE_FOLLOWUP = Skill(
    name="schedule_followup",
    title="Schedule a Follow-up",
    description="Find a free 15-minute slot on your calendar and book a follow-up.",
    system_prompt=(
        "You are a scheduling assistant. Using the current datetime, list the user's "
        "upcoming Google Calendar events, find the earliest free 15-minute slot within "
        "normal waking hours (08:00–20:00, today or the next day), and create a calendar "
        "event there that is genuinely useful to open later — not a bare placeholder:\n"
        "- Title: short and specific to what this follow-up is about, drawn from the "
        "provided context (e.g. 'Follow-up: Resolve AI interview prep'). Never title it "
        "just 'Follow-up' if the context gives you anything more specific to name it after.\n"
        "- Description: carry over everything from the context needed to act without "
        "re-reading the original result — the key facts and every link/URL, verbatim. If "
        "the context is empty, leave the description minimal instead of inventing content.\n"
        "Confirm the exact time you booked, the title you used, and link to the created "
        "event if a URL is returned."
    ),
    allowed_tools=["list_calendar_events", "create_calendar_event"],
    seed_instruction="Find my next free 15 minutes and book a follow-up reminder.",
    surprise=False,  # writes to the calendar — only run on explicit user request
)

SKILLS: list[Skill] = [
    EMAIL_DIGEST,
    NEWS_FOR_YOU,
    TODAYS_PLAN,
    LATEST_PAPERS,
    LATEST_FUNDED_STARTUPS,
    SCHEDULE_FOLLOWUP,
]


def enabled_skills() -> list[Skill]:
    return [s for s in SKILLS if s.enabled]


def surprise_skills() -> list[Skill]:
    """Enabled skills eligible for the random Surprise pool (excludes write skills)."""
    return [s for s in enabled_skills() if s.surprise]


def get_skill(name: str) -> Skill:
    for s in SKILLS:
        if s.name == name:
            return s
    raise KeyError(name)


def pick_random_skill(
    rng: random.Random | None = None,
    exclude: set[str] | None = None,
) -> Skill:
    pool = surprise_skills()
    if not pool:
        raise RuntimeError("no enabled skills")
    if exclude:
        fresh = [s for s in pool if s.name not in exclude]
        if fresh:  # fall back to the full pool when everything ran recently
            pool = fresh
    return (rng or random).choice(pool)
