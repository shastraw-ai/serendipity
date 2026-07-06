"""Tool package: assemble the default registry from all tool modules."""
from __future__ import annotations

from .arcade_tools import ARCADE_TOOLS
from .base import Tool
from .local_tools import LOCAL_TOOLS
from .registry import ToolRegistry


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in [*ARCADE_TOOLS, *LOCAL_TOOLS]:
        registry.register(tool)
    return registry


__all__ = ["Tool", "ToolRegistry", "build_registry"]
