"""Event types streamed to the UI during a run (SSE)."""
from __future__ import annotations

from typing import Any, Callable

# An emitter takes an event dict and delivers it to the client (or a test buffer).
Emit = Callable[[dict[str, Any]], None]


def step(message: str, **extra: Any) -> dict[str, Any]:
    return {"type": "step", "message": message, **extra}


def auth_required(tool: str, url: str) -> dict[str, Any]:
    return {"type": "auth_required", "tool": tool, "url": url}


def done(skill: str, output: str, interaction_id: int | None = None) -> dict[str, Any]:
    return {"type": "done", "skill": skill, "output": output, "interaction_id": interaction_id}


def error(message: str) -> dict[str, Any]:
    return {"type": "error", "message": message}
