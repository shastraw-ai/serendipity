# Surprise Me — an agentic assistant

Click **Surprise Me** and the app picks a random *Skill* (an agentic flow) and runs it
against your Google account and the web: summarize recent email, curate news in your
interests, or plan your day from your calendar. Authenticated Google access is brokered
by [Arcade](https://docs.arcade.dev); reasoning is done by Claude.

## How it's built

```
┌──────────────┐   POST /surprise (SSE)   ┌────────────────────────────────────────┐
│ React UI     │ ───────────────────────▶ │ FastAPI                                │
│ 3 panes:     │ ◀─ step / auth / done ── │  pick_random_skill()                   │
│  history     │                          │  orchestrator.run_skill (the loop)     │
│  Surprise    │                          │    ├─ LLM (Claude, swappable)          │
│  interests   │                          │    └─ ToolRegistry.dispatch            │
└──────────────┘                          │         ├─ arcade → Gmail / Calendar   │
                                          │         └─ local  → web_search (ddgs)  │
                                          └────────────────────────────────────────┘
```

**Key ideas**

- **Tool vs. Skill.** A *Tool* is one capability (`list_emails`, `web_search`). A *Skill*
  is a named config of the generic loop — a system prompt + which tools it may use + a
  seed instruction. Each Skill is multi-step by nature: *fetch → reason/summarize → suggest*.
- **Two tool backends, one interface.** `kind="arcade"` tools run through Arcade (which
  handles Google OAuth); `kind="local"` tools are plain Python. The LLM doesn't know the
  difference — the registry routes it (`app/tools/registry.py`). News search is local
  because it isn't tied to your Google account, so there's nothing for Arcade to authorize.
- **Swappable LLM.** The loop speaks a provider-neutral transcript; `app/llm.py` is the
  only file that imports a model SDK. Swap Claude for OpenAI/a local model = one class.
- **Custom loop, no framework.** The standard tool-calling loop lives in
  `app/orchestrator.py` (~1 screen), reused by every Skill.

## Extending it

- **Add a tool** → one `Tool(...)` in `app/tools/arcade_tools.py` or `local_tools.py`.
- **Add a skill** → one `Skill(...)` in `app/skills/registry.py`.
- **Add an LLM provider** → one `LLM` implementation in `app/llm.py`.

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

1. Open the UI, pick a few **interests** (right pane).
2. Click **Surprise Me**. Live progress streams in.
3. The **first time** a skill needs Gmail/Calendar, an **Authorize** link appears — open
   it, approve Google once, and the run continues automatically. Arcade remembers the grant.
4. Results land in **History** (left pane); click any entry to reopen it.

## Tests
```bash
cd backend && source .venv/bin/activate && python -m pytest -q
```
Covers the loop (with a mocked LLM, no network), registry routing, and random selection.

## Notes / next steps

- Single-user demo: one `ARCADE_USER_ID`. Multi-user would key interests/history per user
  and pass the logged-in identity as `user_id` (Arcade is already multi-tenant on that field).
- Arcade Google tool names (`Gmail_ListEmails`, `GoogleCalendar_ListEvents`) and their
  param schemas live in `app/tools/arcade_tools.py`; verify against
  `client.tools.list(...)` if Arcade changes them.
