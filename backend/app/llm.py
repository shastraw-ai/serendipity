"""LLM interface — the single swap point for the reasoning model.

The orchestrator speaks a small provider-neutral transcript format and never imports a
vendor SDK. Swapping Claude for OpenAI or a local model = one more `LLM` implementation,
no orchestrator changes.

Neutral transcript entries:
  {"role": "user", "text": str}
  {"role": "assistant", "raw": <opaque provider content>}   # carried back verbatim
  {"role": "tool_results", "results": [{"id": str, "content": str}]}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from .config import settings


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None  # provider assistant content, appended back into the transcript


class LLM(Protocol):
    def chat(
        self, system: str, transcript: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse: ...


class ClaudeLLM:
    """Anthropic implementation."""

    def __init__(self, model: str | None = None, max_tokens: int = 2048) -> None:
        self.model = model or settings.claude_model
        self.max_tokens = max_tokens

    def chat(
        self, system: str, transcript: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.anthropic_api_key)
        resp = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            tools=tools,
            messages=_to_anthropic(transcript),
        )

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, input=block.input or {}))

        return LLMResponse(text="\n".join(text_parts), tool_calls=tool_calls, raw=resp.content)


def _to_anthropic(transcript: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for entry in transcript:
        role = entry["role"]
        if role == "user":
            messages.append({"role": "user", "content": entry["text"]})
        elif role == "assistant":
            messages.append({"role": "assistant", "content": entry["raw"]})
        elif role == "tool_results":
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": r["id"],
                            "content": _stringify(r["content"]),
                        }
                        for r in entry["results"]
                    ],
                }
            )
    return messages


def _stringify(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, default=str)
