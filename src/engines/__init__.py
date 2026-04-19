"""TTS engine registry.

Usage::

    from src.engines import get_engine, ENGINES

    engine = get_engine("gtts")
    result = engine.convert(text, output_path, lang="vi", speed=1.0)
"""

from __future__ import annotations

from .base import BaseTTSEngine, EngineResult
from .edge import EdgeTTSEngine
from .gtts_engine import GTTSEngine
from .kokoro_engine import KokoroEngine

ENGINES: dict[str, type[BaseTTSEngine]] = {
    "edge-tts": EdgeTTSEngine,
    "gtts":     GTTSEngine,
    "kokoro":   KokoroEngine,
}

DEFAULT_ENGINE = "edge-tts"


def get_engine(name: str) -> BaseTTSEngine:
    """Return an instantiated engine by name.

    Raises:
        ValueError: if *name* is not a registered engine.
    """
    cls = ENGINES.get(name)
    if cls is None:
        available = ", ".join(ENGINES)
        raise ValueError(
            f"Unknown engine '{name}'. Available: {available}"
        )
    return cls()


__all__ = ["ENGINES", "DEFAULT_ENGINE", "get_engine", "BaseTTSEngine", "EngineResult"]
