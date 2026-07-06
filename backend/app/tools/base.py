"""A Tool is one atomic capability plus how to run it.

Two backends:
  - kind="arcade": executed through Arcade (handles Google OAuth + execution).
  - kind="local":  executed by a plain Python function, no auth.

The orchestrator presents every tool to the LLM the same way (name + description +
input_schema). The registry routes execution by kind. Adding a capability = one Tool.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

ToolKind = Literal["arcade", "local"]


@dataclass(frozen=True)
class Tool:
    name: str  # name exposed to the LLM
    description: str
    input_schema: dict[str, Any]  # JSON Schema for the tool input
    kind: ToolKind
    arcade_name: Optional[str] = None  # e.g. "Gmail_ListEmails" (kind="arcade")
    fn: Optional[Callable[[dict[str, Any]], Any]] = None  # (kind="local")

    def to_llm_schema(self) -> dict[str, Any]:
        """Anthropic tool definition."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }
