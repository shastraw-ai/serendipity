"""A Skill is a named configuration of the generic loop."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Skill:
    name: str  # stable id
    title: str  # shown in the UI
    description: str
    system_prompt: str
    allowed_tools: list[str]  # tool names the loop may use
    seed_instruction: str  # first user turn that kicks off the flow
    enabled: bool = True
    uses_interests: bool = False  # inject the user's interests into the system prompt
    sample_one_interest: bool = False  # narrow interests to one random pick before the run
    surprise: bool = True  # eligible for the random "Surprise Me" pool (writes opt out)

    def public(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "enabled": self.enabled,
            "surprise": self.surprise,
        }
