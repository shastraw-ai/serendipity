"""Loop + registry + selection tests. No network: the LLM and tools are fakes."""
from __future__ import annotations

import random

from app.events import step
from app.llm import LLMResponse, ToolCall
from app.orchestrator import run_skill
from app.skills.base import Skill
from app.skills.registry import enabled_skills, pick_random_skill
from app.tools.base import Tool
from app.tools.registry import ToolRegistry


class FakeLLM:
    """Calls one tool on the first turn, then returns a final answer."""

    def chat(self, system, transcript, tools):
        already_ran_tool = any(e["role"] == "tool_results" for e in transcript)
        if already_ran_tool:
            return LLMResponse(text="Here is your summary.", raw="final")
        return LLMResponse(
            text="Let me check.",
            tool_calls=[ToolCall(id="t1", name="echo", input={"q": "hi"})],
            raw="assistant-turn",
        )


def _registry_with_echo() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="echo",
            description="echo input",
            kind="local",
            fn=lambda i: {"echoed": i},
            input_schema={"type": "object", "properties": {"q": {"type": "string"}}},
        )
    )
    return reg


def _skill() -> Skill:
    return Skill(
        name="t",
        title="Test",
        description="d",
        system_prompt="p",
        allowed_tools=["echo"],
        seed_instruction="go",
    )


def test_run_skill_executes_tool_then_finishes():
    events = []
    result = run_skill(
        _skill(),
        user_id="u",
        emit=events.append,
        llm=FakeLLM(),
        registry=_registry_with_echo(),
        interests=["Tech"],
        now_iso="2026-07-05T09:00:00",
    )
    assert result.output == "Here is your summary."
    assert result.steps == [{"tool": "echo", "input": {"q": "hi"}}]
    assert any(e["type"] == "step" for e in events)


def test_registry_dispatch_routes_local():
    reg = _registry_with_echo()
    out = reg.dispatch("echo", {"q": "x"}, user_id="u", emit=lambda e: None)
    assert out == {"echoed": {"q": "x"}}


def test_pick_random_skill_only_enabled():
    rng = random.Random(0)
    names = {pick_random_skill(rng).name for _ in range(50)}
    assert names <= {s.name for s in enabled_skills()}
