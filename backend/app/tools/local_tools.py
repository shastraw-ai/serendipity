"""Local tools — plain Python, no auth, no Arcade.

`web_search` fetches news/web results via DuckDuckGo (`ddgs`); `fetch_url` reads one
page's text so a skill can go a level deeper than a snippet. Neither is tied to the
user's Google account, so there's nothing to authenticate — local tools are the right
fit. Swap the provider (e.g. Tavily) here without touching the orchestrator.
"""
from __future__ import annotations

import re
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

_TAG_RE = re.compile(r"(?is)<(script|style).*?</\1>|<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _fetch_url(tool_input: dict[str, Any]) -> Any:
    url = (tool_input.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"error": "url must start with http:// or https://"}
    max_chars = int(tool_input.get("max_chars", 4000))

    import httpx

    try:
        resp = httpx.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (SurpriseMe news reader)"},
        )
        resp.raise_for_status()
    except Exception as exc:  # network/HTTP errors surface to the model, not a crash
        return {"error": f"fetch failed: {exc}"}

    text = _WS_RE.sub(" ", _TAG_RE.sub(" ", resp.text)).strip()
    return {"url": str(resp.url), "text": text[:max_chars]}


FETCH_URL = Tool(
    name="fetch_url",
    description=(
        "Fetch one web page and return its readable text (HTML stripped). Use to read a "
        "specific article in full — going deeper than a search snippet."
    ),
    kind="local",
    fn=_fetch_url,
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The page URL (http/https)."},
            "max_chars": {
                "type": "integer",
                "description": "Max characters of text to return.",
                "default": 4000,
            },
        },
        "required": ["url"],
        "additionalProperties": False,
    },
)

LOCAL_TOOLS = [WEB_SEARCH, FETCH_URL]
