"""Loop + registry + selection tests. No network: the LLM and tools are fakes."""
from __future__ import annotations

import random

from app.events import step
from app.llm import LLMResponse, ToolCall
from app.orchestrator import MAX_ITERATIONS, _split_title, run_skill
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


def test_split_title_extracts_title_line():
    title, output = _split_title("Title: My Run\n\nBody text here.", fallback="Fallback")
    assert title == "My Run"
    assert output == "Body text here."


def test_split_title_falls_back_without_title_line():
    text = "Just body text, no title line."
    title, output = _split_title(text, fallback="Fallback")
    assert title == "Fallback"
    assert output == text


def test_split_title_falls_back_on_empty_title():
    title, output = _split_title("Title: \n\nBody text.", fallback="Fallback")
    assert title == "Fallback"
    assert output == "Body text."


class CapturingLLM:
    """Returns immediately with no tool calls; records the transcript it was given."""

    def __init__(self):
        self.seen_transcript = None

    def chat(self, system, transcript, tools):
        self.seen_transcript = transcript
        return LLMResponse(text="Title: Done\n\nAll set.", raw="final")


def _calendar_skill() -> Skill:
    return Skill(
        name="cal",
        title="Cal Skill",
        description="d",
        system_prompt="p",
        allowed_tools=["list_calendar_events"],
        seed_instruction="go",
    )


def _registry_with_calendar_tool() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="list_calendar_events",
            description="d",
            kind="local",
            fn=lambda i: [],
            input_schema={"type": "object", "properties": {}},
        )
    )
    return reg


def test_run_skill_prepends_datetime_for_calendar_tools():
    llm = CapturingLLM()
    run_skill(
        _calendar_skill(),
        user_id="u",
        emit=lambda e: None,
        llm=llm,
        registry=_registry_with_calendar_tool(),
        interests=[],
        now_iso="2026-07-06T18:30:00",
    )
    seed = llm.seen_transcript[0]["text"]
    assert seed.startswith("Current datetime (ISO-8601, local): 2026-07-06T18:30:00")
    assert seed.endswith("go")


class NeverFinishingLLM:
    """Always wants to call another tool — until no tools are offered, at which
    point it's forced to answer. Mirrors what happens when a run hits MAX_ITERATIONS."""

    def __init__(self):
        self.calls = 0

    def chat(self, system, transcript, tools):
        self.calls += 1
        if not tools:
            return LLMResponse(text="Title: Partial\n\nHere's what I found so far.", raw="final")
        return LLMResponse(
            text="Checking again.",
            tool_calls=[ToolCall(id=f"t{self.calls}", name="echo", input={"q": "hi"})],
            raw="assistant-turn",
        )


def test_run_skill_forces_final_answer_after_max_iterations():
    llm = NeverFinishingLLM()
    events = []
    result = run_skill(
        _skill(),
        user_id="u",
        emit=events.append,
        llm=llm,
        registry=_registry_with_echo(),
        interests=[],
        now_iso="2026-07-05T09:00:00",
    )
    assert result.title == "Partial"
    assert result.output == "Here's what I found so far."
    # MAX_ITERATIONS normal rounds (all offering tools) + one forced final round (no tools)
    assert llm.calls == MAX_ITERATIONS + 1
    assert any("Wrapping up" in e.get("message", "") for e in events)
