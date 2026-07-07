"""FastAPI app: SSE-streamed Surprise runs + history/interests/skills endpoints."""
from __future__ import annotations

import asyncio
import json
import queue
import random
import threading
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import store
from .config import settings
from .events import done, error, step
from .llm import ClaudeLLM
from .orchestrator import run_skill
from .skills.registry import SKILLS, get_skill, pick_random_skill
from .tools import build_registry

app = FastAPI(title="Surprise Me")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo; single local user
    allow_methods=["*"],
    allow_headers=["*"],
)

REGISTRY = build_registry()


@app.on_event("startup")
def _startup() -> None:
    store.init_db()


def _run_worker(q: "queue.Queue", skill, note: str | None = None) -> None:
    """Blocking worker: run one skill's loop, pushing events onto the queue.

    Runs in a thread so the SSE generator can stream events while Arcade's
    OAuth wait / tool calls block.
    """
    def emit(ev: dict) -> None:
        q.put(ev)

    try:
        interests = store.get_interests(settings.user_id)
        if skill.sample_one_interest and interests:
            interests = [random.choice(interests)]
            emit(step(f"Focusing on: {interests[0]}", skill=skill.name))
        now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
        result = run_skill(
            skill,
            user_id=settings.user_id,
            emit=emit,
            llm=ClaudeLLM(),
            registry=REGISTRY,
            interests=interests,
            now_iso=now_iso,
            extra_context=note,
        )
        interaction_id = store.save_interaction(
            result.skill, result.title, result.output, result.steps
        )
        emit(done(result.skill, result.title, result.output, interaction_id))
    except Exception as exc:  # noqa: BLE001 — surface any failure to the client
        emit(error(str(exc)))
    finally:
        q.put(None)  # sentinel: stream complete


def _stream(skill, note: str | None = None) -> StreamingResponse:
    q: "queue.Queue" = queue.Queue()
    threading.Thread(target=_run_worker, args=(q, skill, note), daemon=True).start()

    async def gen():
        while True:
            ev = await asyncio.to_thread(q.get)
            if ev is None:
                break
            yield f"data: {json.dumps(ev)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/surprise")
async def surprise() -> StreamingResponse:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    skill = pick_random_skill(exclude=store.skills_run_since(cutoff))
    return _stream(skill)


class RunBody(BaseModel):
    note: str | None = None


@app.post("/skills/{name}/run")
async def run_named_skill(name: str, body: RunBody | None = None) -> StreamingResponse:
    """Run one named skill directly (e.g. the user-triggered follow-up)."""
    try:
        skill = get_skill(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown skill")
    if not skill.enabled:
        raise HTTPException(status_code=400, detail="skill disabled")
    return _stream(skill, note=(body.note if body else None))


@app.get("/skills")
def list_skills() -> list[dict]:
    return [s.public() for s in SKILLS]


@app.get("/interactions")
def list_interactions() -> list[dict]:
    return store.list_interactions()


@app.get("/interactions/{interaction_id}")
def get_interaction(interaction_id: int) -> dict:
    row = store.get_interaction(interaction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return row


class InterestsBody(BaseModel):
    items: list[str]


@app.get("/interests")
def get_interests() -> dict:
    return {"items": store.get_interests(settings.user_id)}


@app.put("/interests")
def put_interests(body: InterestsBody) -> dict:
    return {"items": store.set_interests(settings.user_id, body.items)}
