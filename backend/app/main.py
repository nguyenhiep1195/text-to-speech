"""FastAPI application factory for TTS Studio backend."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure backend root is on sys.path so `src.*` imports resolve
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_cors_origins
from .routes.tts_routes import router as tts_router
from .routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="TTS Studio API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(tts_router, prefix="/api")

    return app


app = create_app()
