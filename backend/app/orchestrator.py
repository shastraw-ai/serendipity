"""The generic agentic loop, shared by every Skill.

A Skill is just a configuration of this loop (system prompt + allowed tools + seed
instruction). The loop drives the LLM, executes whatever tools it asks for via the
registry, and streams progress. It is provider-agnostic and side-effect free except for
the tools it runs and the events it emits.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .events import Emit, step
from .llm import LLM
from .skills.base import Skill
from .tools.registry import ToolRegistry

MAX_ITERATIONS = 6  # safety bound on tool round-trips


@dataclass
class RunResult:
    skill: str
    output: str
    steps: list[dict[str, Any]]


def build_system_prompt(skill: Skill, interests: list[str], now_iso: str) -> str:
    interests_block = ""
    if skill.uses_interests:
        interests_line = ", ".join(interests) if interests else "(none configured)"
        interests_block = f"User interests: {interests_line}\n"
    return (
        f"{skill.system_prompt}\n\n"
        f"Current datetime (ISO-8601, local): {now_iso}\n"
        f"{interests_block}\n"
        "Use the provided tools to gather real data before answering — do not invent "
        "emails, events, or news. If, while working, another available tool would add "
        "concrete information the user clearly wants (e.g. an email mentions a meeting and "
        "you can check the calendar for a conflict), call it — but only when it genuinely "
        "helps; don't over-fetch.\n\n"
        "When your summary references a specific source, link to it inline in Markdown "
        "([text](url)) using a real URL from the tool results — a web result's `url`, or for "
        "a Gmail message its `id` as https://mail.google.com/mail/u/0/#all/<id>. Never "
        "fabricate a link; omit it if you don't have one.\n\n"
        "When you have enough, reply with a concise, friendly Markdown summary for the user. "
        "End with a short 'Suggested next step' line."
    )


def run_skill(
    skill: Skill,
    *,
    user_id: str,
    emit: Emit,
    llm: LLM,
    registry: ToolRegistry,
    interests: list[str],
    now_iso: str,
    extra_context: str | None = None,
) -> RunResult:
    emit(step(f"Starting: {skill.title}", skill=skill.name))
    system = build_system_prompt(skill, interests, now_iso)
    seed = skill.seed_instruction
    if extra_context:
        seed = f"{seed}\n\nContext: {extra_context}"
    transcript: list[dict[str, Any]] = [{"role": "user", "text": seed}]
    tool_schemas = registry.schemas_for(skill.allowed_tools)
    steps: list[dict[str, Any]] = []

    for _ in range(MAX_ITERATIONS):
        resp = llm.chat(system, transcript, tool_schemas)
        transcript.append({"role": "assistant", "raw": resp.raw})

        if resp.text and resp.tool_calls:
            emit(step(resp.text))  # the model's narration between tool calls

        if not resp.tool_calls:
            return RunResult(skill=skill.name, output=resp.text, steps=steps)

        results = []
        for call in resp.tool_calls:
            try:
                output = registry.dispatch(call.name, call.input, user_id, emit)
            except Exception as exc:  # surface tool failure to the model, keep going
                output = {"error": str(exc)}
                emit(step(f"{call.name} failed: {exc}", tool=call.name))
            steps.append({"tool": call.name, "input": call.input})
            results.append({"id": call.id, "content": output})
        transcript.append({"role": "tool_results", "results": results})

    return RunResult(
        skill=skill.name,
        output="I couldn't finish within the step limit. Try again.",
        steps=steps,
    )
