# Surprise Me

Agentic assistant: a "Surprise Me" button runs a random *Skill* (an agentic flow) against
the user's Google account and the web — email digest, news in interests, or today's plan.
Google access is brokered by [Arcade](https://docs.arcade.dev); reasoning is Claude.

## Layout
- `backend/` — FastAPI + a custom tool-calling loop. Python venv at `backend/.venv`.
- `frontend/` — Vite + React + TS, 3-pane UI (history · Surprise · interests).

## Core model — Tool vs. Skill
- **Tool** = one capability + how to run it (`app/tools/`). Two backends:
  - `kind="arcade"` → executed via Arcade (handles Google OAuth). e.g. `Gmail_ListEmails`.
  - `kind="local"` → plain Python fn, no auth. e.g. `web_search` (DuckDuckGo/`ddgs`).
- **Skill** = a named config of the generic loop (`app/skills/`): system prompt + allowed
  tools + seed instruction. Skills are multi-step by nature: fetch → reason → suggest.
  - `surprise=False` keeps a skill out of the random pool — use it for any skill with side
    effects (e.g. `schedule_followup`, which writes a calendar event). Such skills run only
    via `POST /skills/{name}/run` (explicit user action), never from a random Surprise.
  - A read skill may list complementary read-only tools in `allowed_tools`; the shared
    prompt lets the model call a second one mid-run when it adds concrete info (e.g. an
    email implies a conflict → check the calendar).
- `app/orchestrator.py` holds the ONE loop every Skill reuses. It is provider-neutral and
  never imports a model SDK.

## Conventions
- **Extend, don't rebuild**: new tool = one `Tool(...)` in `tools/arcade_tools.py` or
  `local_tools.py`; new skill = one `Skill(...)` in `skills/registry.py`; new LLM provider =
  one class in `app/llm.py` (the only file that imports a model SDK).
- The registry (`tools/registry.py`) is the single place that routes arcade vs. local and
  handles Arcade authorize→wait→execute. Keep auth logic out of the orchestrator and skills.
- Run progress is streamed to the UI as SSE events built by `app/events.py`
  (`step` / `auth_required` / `done` / `error`). Emit through these, don't hand-roll dicts.
- Anything needing the user's Google account goes through Arcade; anything unauthenticated
  (web/news) is a local tool.
- Random Surprise selection (`skills/registry.py`) draws from `surprise_skills()` and skips
  skills run in the last hour (`store.skills_run_since`), falling back to the full pool if
  all are excluded.
- Single-user demo: one `ARCADE_USER_ID`. Arcade is multi-tenant on `user_id` — a real
  multi-user version keys history/interests and tool auth on the logged-in identity.

## Commands
```bash
# backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
python -m pytest -q                     # loop/registry/selection tests (mocked LLM, no network)

# frontend
cd frontend && npm run dev              # :5173, proxies /api → :8000
npm run build                           # tsc typecheck + vite build
```

## Config
`backend/.env` (from `.env.example`): `ARCADE_API_KEY`, `ANTHROPIC_API_KEY`,
`ARCADE_USER_ID` (Google email to authorize), optional `CLAUDE_MODEL`, `DB_PATH`.

## Gotchas
- Arcade Google tool names/param schemas are hardcoded in `tools/arcade_tools.py` from the
  docs. If Arcade renames a param, fix it there; verify with `client.tools.list(...)`.
- `/surprise` runs the blocking loop in a worker thread and streams events via a queue, so
  Arcade's OAuth `wait_for_completion` doesn't block the SSE response.
- SQLite history/interests persist in `backend/surprise.db` (gitignored).
