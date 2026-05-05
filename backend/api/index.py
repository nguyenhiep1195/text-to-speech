"""Vercel serverless entry point.

Wraps the FastAPI app with Mangum so it runs as an AWS Lambda-compatible
handler (which Vercel's Python runtime expects).
"""

import sys
from pathlib import Path

# Ensure the backend root is importable
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
