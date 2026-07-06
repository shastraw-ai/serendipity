"""Registry that holds every Tool and routes execution by backend.

`dispatch` is the single choke point where an arcade tool gets authorized+executed
and a local tool just gets called. This is what keeps "is it Arcade or local?" out of
the orchestrator and out of the LLM's awareness.
"""
from __future__ import annotations

import json
from typing import Any

from ..events import Emit, auth_required, step
from .base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def schemas_for(self, names: list[str]) -> list[dict[str, Any]]:
        return [self._tools[n].to_llm_schema() for n in names]

    def dispatch(self, name: str, tool_input: dict[str, Any], user_id: str, emit: Emit) -> Any:
        """Run a tool by name and return its result (JSON-serializable)."""
        tool = self._tools[name]
        if tool.kind == "local":
            emit(step(f"Running {name}", tool=name))
            assert tool.fn is not None
            return tool.fn(tool_input)
        return self._run_arcade(tool, tool_input, user_id, emit)

    def _run_arcade(self, tool: Tool, tool_input: dict[str, Any], user_id: str, emit: Emit) -> Any:
        from ..arcade_client import get_arcade

        client = get_arcade()
        arcade_name = tool.arcade_name
        assert arcade_name is not None

        # 1) Ensure the user has authorized this tool (Google OAuth via Arcade).
        auth = client.tools.authorize(tool_name=arcade_name, user_id=user_id)
        if getattr(auth, "status", None) != "completed":
            emit(auth_required(tool.name, auth.url))
            client.auth.wait_for_completion(auth.id)  # blocks until user approves

        # 2) Execute.
        emit(step(f"Calling {tool.name}", tool=tool.name))
        result = client.tools.execute(tool_name=arcade_name, input=tool_input, user_id=user_id)
        return _unwrap(result)


def _unwrap(result: Any) -> Any:
    """Pull the useful payload out of an Arcade execute response."""
    output = getattr(result, "output", None)
    if output is not None:
        value = getattr(output, "value", None)
        if value is not None:
            return value
        error = getattr(output, "error", None)
        if error is not None:
            return {"error": str(error)}
    # Fallback: best-effort serialization.
    try:
        return json.loads(result.model_dump_json())
    except Exception:
        return str(result)
