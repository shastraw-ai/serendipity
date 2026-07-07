"""pick_random_skill's exclude/fallback behavior. No network."""
from __future__ import annotations

import random

from app.skills.registry import pick_random_skill, surprise_skills


def test_pick_random_skill_excludes_named_skills():
    rng = random.Random(1)
    all_names = {s.name for s in surprise_skills()}
    excluded = {next(iter(all_names))}
    picks = {pick_random_skill(rng, exclude=excluded).name for _ in range(50)}
    assert picks <= all_names - excluded
    assert picks  # sanity: something was actually picked


def test_pick_random_skill_falls_back_to_full_pool_when_all_excluded():
    rng = random.Random(2)
    all_names = {s.name for s in surprise_skills()}
    picks = {pick_random_skill(rng, exclude=all_names).name for _ in range(50)}
    # Excluding everything leaves nothing "fresh", so selection falls back to the
    # full surprise pool rather than raising or excluding forever.
    assert picks <= all_names
    assert picks
