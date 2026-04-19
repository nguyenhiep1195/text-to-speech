"""Shared types used by all TTS engine implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EngineResult:
    """Unified result object returned by every engine.

    Attributes:
        audio_path:  Path to the generated audio file.
        boundaries:  Timing data list.  Each entry is a dict:
                     ``{"text": str, "offset_ms": float, "duration_ms": float,
                        "boundary_type": str}``.
                     Engines that cannot provide timing data return an empty list.
    """

    audio_path: Path
    boundaries: list[dict] = field(default_factory=list)


class BaseTTSEngine(ABC):
    """Abstract base class every TTS engine must implement."""

    #: Human-readable name shown in logs / help text
    name: str = "base"

    @abstractmethod
    def convert(
        self,
        text: str,
        output_path: Path,
        *,
        lang: str = "vi",
        speed: float = 1.0,
        **kwargs,
    ) -> EngineResult:
        """Convert *text* to speech and save to *output_path*.

        Args:
            text:        Input text.
            output_path: Destination file (extension determined by engine).
            lang:        ISO 639-1 language code (``"vi"``, ``"en"`` …).
            speed:       Playback speed multiplier (1.0 = normal).
            **kwargs:    Engine-specific parameters.

        Returns:
            :class:`EngineResult` with audio path and optional timing data.
        """
