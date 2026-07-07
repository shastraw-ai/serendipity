# Surprise Me — an agentic assistant

Click **Surprise Me** and the app picks a random *Skill* (an agentic flow) and runs it
against your Google account and the web: summarize recent email, curate a deep dive into
one story or paper or funded startup, or plan your day from your calendar. Authenticated
Google access is brokered by [Arcade](https://docs.arcade.dev); reasoning is done by Claude.

## How it's built

```
┌──────────────┐  POST /surprise (SSE)            ┌───────────────────────────────────────────┐
│ React UI     │ ────────────────────────────────▶│ FastAPI                                   │
│ 3 panes:     │◀── step / auth_required / done ──│  pick_random_skill()                      │
│  history     │  POST /skills/{name}/run          │  orchestrator.run_skill (the loop)        │
│  Surprise    │ ────────────────────────────────▶│    ├─ LLM (Claude, swappable)              │
│  interests   │                                   │    └─ ToolRegistry.dispatch                │
└──────────────┘                                   │         ├─ arcade → Gmail / Calendar       │
                                                    │         └─ local  → web_search, fetch_url  │
                                                    └───────────────────────────────────────────┘
```

**Key ideas**

- **Tool vs. Skill.** A *Tool* is one capability (`list_emails`, `web_search`). A *Skill*
  is a named config of the generic loop — a system prompt + which tools it may use + a
  seed instruction. Each Skill is multi-step by nature: *fetch → reason/summarize → suggest*.
- **Two tool backends, one interface.** `kind="arcade"` tools run through Arcade (which
  handles Google OAuth); `kind="local"` tools are plain Python. The LLM doesn't know the
  difference — the registry routes it (`app/tools/registry.py`). Web search and page
  fetching are local because they aren't tied to your Google account, so there's nothing
  for Arcade to authorize.
- **Swappable LLM.** The loop speaks a provider-neutral transcript; `app/llm.py` is the
  only file that imports a model SDK. Swap Claude for OpenAI/a local model = one class.
- **Custom loop, no framework.** The standard tool-calling loop lives in
  `app/orchestrator.py` (~1 screen), reused by every Skill.
- **Read vs. write skills.** `Skill.surprise` marks whether it's eligible for the random
  pool. Side-effecting skills (e.g. `schedule_followup`, which books a calendar event) set
  `surprise=False` — they never run randomly, only via explicit user action
  (`POST /skills/{name}/run`), which is how the UI's dropdown and follow-up button reach them.
- **Interests are opt-in per skill.** `uses_interests` gates whether the system prompt gets
  the user's interests at all — only the news skill needs them today, so email/calendar
  skills never see them. `sample_one_interest` narrows to one random interest per run, so a
  single-story deep dive doesn't try to cover every interest at once.
- **Won't repeat itself within the hour.** Random selection (`pick_random_skill`) excludes
  skills that already ran in the last hour (`store.skills_run_since`), falling back to the
  full pool if everything's been run recently.
- **Titles come from the run, not the skill.** The model's final answer starts with a
  `Title: ...` line naming that specific run's content (e.g. "Resolve AI interview
  follow-up"); `orchestrator._split_title` parses it off and it becomes the interaction's
  title, so History reads like a real log instead of a repeated list of skill names.

## The skills today

| Skill | Tools | Notes |
|---|---|---|
| Email Digest | Gmail, Calendar | Triages recent email, flags what to act on. |
| News For You | web search, fetch page | Picks one interest at random, one top story, reads it in full. |
| Today's Plan | Calendar, Gmail | Summarizes today; if it's evening and today's done, previews tomorrow too. |
| Latest Papers | web search, fetch page | One notable recent paper, explained. |
| Latest Funded Startups | web search, fetch page | One notable recent funding round, explained. |
| Schedule a Follow-up | Calendar (read + **write**) | Books a 15-min slot from real context; user-triggered only, never in the random pool. |

## Extending it

- **Add a tool** → one `Tool(...)` in `app/tools/arcade_tools.py` or `local_tools.py`.
- **Add a skill** → one `Skill(...)` in `app/skills/registry.py`.
- **Add an LLM provider** → one `LLM` implementation in `app/llm.py`.

## UI features

- **Split "Surprise Me" button** — click it to run a random eligible skill, or use the
  attached ▾ dropdown to run one specific skill directly.
- **Follow-up on a result** — after a run, "📅 Find me 15 min & schedule a follow-up" books
  a calendar event whose title and description are generated from that run's actual
  content (its title and full output, including any links) — not a generic placeholder.
- **Ask a follow-up** — a free-text box under any result re-runs the same skill fresh with
  your question folded in as context.
- **History, grouped by day** — the left pane groups past runs under collapsible
  "Today / Yesterday / \<date\>" headers.

## Setup

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ARCADE_API_KEY, ANTHROPIC_API_KEY, ARCADE_USER_ID
uvicorn app.main:app --reload --port 8000
```
- `ARCADE_API_KEY` — from the [Arcade dashboard](https://api.arcade.dev).
- `ANTHROPIC_API_KEY` — from the [Anthropic console](https://console.anthropic.com).
- `ARCADE_USER_ID` — the email of the Google account you'll authorize.

### Frontend
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173  (proxies /api → :8000)
```

## Using it

1. Open the UI, pick a few **interests** (right pane) — only skills that need them use them.
2. Click **Surprise Me** for a random skill, or pick one from the ▾ dropdown. Live progress
   streams in as a single rolling line (expandable to the full step list).
3. The **first time** a skill needs Gmail/Calendar, an **Authorize** link appears — open
   it, approve Google once, and the run continues automatically. Arcade remembers the grant.
4. On a finished result: ask a free-text follow-up, or (if offered) schedule a calendar
   follow-up from it.
5. Results land in **History** (left pane), grouped by day; click any entry to reopen it.

## Tests
```bash
cd backend && source .venv/bin/activate && python -m pytest -q
```
Covers the loop (with a mocked LLM, no network), registry routing, and random selection.

## Notes / next steps

- Single-user demo: one `ARCADE_USER_ID`. Multi-user would key interests/history per user
  and pass the logged-in identity as `user_id` (Arcade is already multi-tenant on that field).
- Arcade Google tool names (`Gmail_ListEmails`, `GoogleCalendar_ListEvents`,
  `GoogleCalendar_CreateEvent`) and their param schemas live in `app/tools/arcade_tools.py`;
  verify against `client.tools.list(...)` if Arcade changes them.
- `fetch_url` (local tool) strips HTML client-side and caps text length — it's meant for
  going one level deeper than a search snippet, not general scraping.
