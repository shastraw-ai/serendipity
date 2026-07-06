"""Environment-backed settings. Loaded once at import."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    arcade_api_key: str = os.getenv("ARCADE_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Single-user demo: the identity Arcade authorizes Google access against.
    user_id: str = os.getenv("ARCADE_USER_ID", "demo@example.com")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
    db_path: str = os.getenv("DB_PATH", "surprise.db")


settings = Settings()
