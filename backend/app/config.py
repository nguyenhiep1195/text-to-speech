"""Environment-based configuration."""

from __future__ import annotations

import os


def get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))
