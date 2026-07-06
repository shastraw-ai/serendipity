"""Thin wrapper around the Arcade client.

Lazily constructed so the app (and unit tests) can import modules without an API key.
"""
from __future__ import annotations

from functools import lru_cache

from arcadepy import Arcade

from .config import settings


@lru_cache(maxsize=1)
def get_arcade() -> Arcade:
    if not settings.arcade_api_key:
        raise RuntimeError("ARCADE_API_KEY is not set — copy .env.example to .env and fill it in.")
    return Arcade(api_key=settings.arcade_api_key)
