"""SQLite persistence tests. Redirects store.settings to a temp file — no real DB touched.

store.py's functions read `settings.db_path` fresh on every call (a module-level global
imported into store.py), so swapping that reference for the test's duration is enough to
redirect every function here without any test-only parameters in production code.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app import store


@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "settings", replace(store.settings, db_path=str(tmp_path / "test.db")))
    store.init_db()
    return store


def test_init_db_is_idempotent(temp_store):
    temp_store.init_db()  # calling twice must not raise
    assert temp_store.list_interactions() == []


def test_save_list_get_interaction_roundtrip(temp_store):
    interaction_id = temp_store.save_interaction(
        "email_digest", "My Title", "The output body", [{"tool": "list_emails", "input": {}}]
    )

    listed = temp_store.list_interactions()
    assert len(listed) == 1
    assert listed[0]["id"] == interaction_id
    assert listed[0]["skill"] == "email_digest"
    assert listed[0]["title"] == "My Title"

    detail = temp_store.get_interaction(interaction_id)
    assert detail["output"] == "The output body"
    assert detail["steps"] == [{"tool": "list_emails", "input": {}}]

    assert temp_store.get_interaction(interaction_id + 999) is None


def test_skills_run_since_filters_by_cutoff(temp_store):
    temp_store.save_interaction("email_digest", "T", "O", [])
    past_cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    future_cutoff = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    assert "email_digest" in temp_store.skills_run_since(past_cutoff)
    assert "email_digest" not in temp_store.skills_run_since(future_cutoff)


def test_interests_default_then_roundtrip(temp_store):
    assert temp_store.get_interests("user@example.com") == store.DEFAULT_INTERESTS

    saved = temp_store.set_interests("user@example.com", ["Tech", "  ", "Finance", ""])
    assert saved == ["Tech", "Finance"]
    assert temp_store.get_interests("user@example.com") == ["Tech", "Finance"]
