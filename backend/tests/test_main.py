"""FastAPI endpoint contract tests.

Only routes that error out or do plain CRUD before ever reaching run_skill's background
thread are exercised here — no live LLM/Arcade calls. store.settings is redirected to a
temp DB (same pattern as test_store.py) so the real backend/surprise.db is never touched.
"""
from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app import main, store
from app.skills.registry import SKILLS, get_skill


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "settings", replace(store.settings, db_path=str(tmp_path / "test.db")))
    with TestClient(main.app) as c:
        yield c


def test_list_skills_matches_registry(client):
    resp = client.get("/skills")
    assert resp.status_code == 200
    names = {s["name"] for s in resp.json()}
    assert names == {s.name for s in SKILLS}


def test_run_unknown_skill_returns_404(client):
    resp = client.post("/skills/does-not-exist/run", json={})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "unknown skill"


def test_run_disabled_skill_returns_400(client, monkeypatch):
    disabled = replace(get_skill("email_digest"), enabled=False)
    monkeypatch.setattr(main, "get_skill", lambda name: disabled)
    resp = client.post("/skills/email_digest/run", json={})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "skill disabled"


def test_interests_roundtrip(client):
    resp = client.put("/interests", json={"items": ["Tech", " ", "Finance"]})
    assert resp.status_code == 200
    assert resp.json() == {"items": ["Tech", "Finance"]}

    resp = client.get("/interests")
    assert resp.status_code == 200
    assert resp.json() == {"items": ["Tech", "Finance"]}
