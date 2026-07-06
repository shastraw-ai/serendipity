"""Local tools — plain Python, no auth, no Arcade.

`web_search` fetches news/web results via DuckDuckGo (`ddgs`). News isn't tied to the
user's Google account, so there's nothing to authenticate — a local tool is the right
fit. Swap the provider (e.g. Tavily) here without touching the orchestrator.
"""
from __future__ import annotations

from typing import Any

from .base import Tool


def _web_search(tool_input: dict[str, Any]) -> Any:
    query = (tool_input.get("query") or "").strip()
    max_results = int(tool_input.get("max_results", 6))
    if not query:
        return {"error": "query is required"}

    from ddgs import DDGS

    with DDGS() as ddgs:
        hits = ddgs.text(query, max_results=max_results)

    return [
        {"title": h.get("title"), "url": h.get("href"), "snippet": h.get("body")}
        for h in hits
    ]


WEB_SEARCH = Tool(
    name="web_search",
    description=(
        "Search the web for recent news/articles on a topic. Returns titles, URLs, and "
        "snippets. Use for news in the user's interests."
    ),
    kind="local",
    fn=_web_search,
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query."},
            "max_results": {"type": "integer", "default": 6},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
)

LOCAL_TOOLS = [WEB_SEARCH]
