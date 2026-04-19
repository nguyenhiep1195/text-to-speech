"""Vercel serverless entry point for the TTS FastAPI app."""
from app.main import app  # noqa: F401 – Vercel expects an ASGI/WSGI app named `app`
