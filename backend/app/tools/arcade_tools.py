"""Arcade-backed tools (authenticated, per-user Google access).

Tool names + params follow Arcade's Google toolkits. If Arcade renames a param, the
schemas below are the single place to adjust. `additionalProperties: True` keeps the
LLM from being blocked by a field we didn't enumerate. Verify names/params at runtime
with `client.tools.list(...)` — see README.
"""
from __future__ import annotations

from .base import Tool

GMAIL_LIST_EMAILS = Tool(
    name="list_emails",
    description=(
        "List the user's most recent Gmail messages (sender, subject, snippet, date). "
        "Use to read/summarize recent email."
    ),
    kind="arcade",
    arcade_name="Gmail_ListEmails",
    input_schema={
        "type": "object",
        "properties": {
            "n_emails": {
                "type": "integer",
                "description": "How many recent emails to fetch (1-25).",
                "default": 10,
            },
        },
        "additionalProperties": True,
    },
)

CALENDAR_LIST_EVENTS = Tool(
    name="list_calendar_events",
    description=(
        "List Google Calendar events in a time window. Pass ISO-8601 datetimes. "
        "Use to read the user's schedule for a day."
    ),
    kind="arcade",
    arcade_name="GoogleCalendar_ListEvents",
    input_schema={
        "type": "object",
        "properties": {
            "min_end_datetime": {
                "type": "string",
                "description": "Only events ending after this ISO-8601 datetime (e.g. 2026-07-05T00:00:00).",
            },
            "max_start_datetime": {
                "type": "string",
                "description": "Only events starting before this ISO-8601 datetime.",
            },
            "max_results": {"type": "integer", "default": 25},
        },
        "required": ["min_end_datetime", "max_start_datetime"],
        "additionalProperties": True,
    },
)

CALENDAR_CREATE_EVENT = Tool(
    name="create_calendar_event",
    description=(
        "Create a Google Calendar event. Pass ISO-8601 start/end datetimes. Use to book a "
        "slot the user asked for (e.g. a 15-minute follow-up you found free time for)."
    ),
    kind="arcade",
    arcade_name="GoogleCalendar_CreateEvent",
    input_schema={
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "Event title."},
            "start_datetime": {
                "type": "string",
                "description": "Start as ISO-8601 (e.g. 2026-07-06T14:00:00).",
            },
            "end_datetime": {
                "type": "string",
                "description": "End as ISO-8601. Make this 15 min after start for a follow-up.",
            },
            "description": {
                "type": "string",
                "description": (
                    "Event notes. Include the full relevant detail and every link/URL from "
                    "context verbatim, not just a short blurb, so the invite is self-contained."
                ),
            },
            "calendar_id": {"type": "string", "default": "primary"},
        },
        "required": ["summary", "start_datetime", "end_datetime"],
        "additionalProperties": True,
    },
)

ARCADE_TOOLS = [GMAIL_LIST_EMAILS, CALENDAR_LIST_EVENTS, CALENDAR_CREATE_EVENT]
