"""TTS engine backed by edge-tts (Microsoft Edge neural voices).

Vietnamese voices available:
  - vi-VN-HoaiMyNeural   (female – default)
  - vi-VN-NamMinhNeural  (male)
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import edge_tts

from .utils import chunk_text, ensure_output_dir

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_VOICE = "vi-VN-HoaiMyNeural"
AVAILABLE_VOICES: dict[str, str] = {
    "vi-female": "vi-VN-HoaiMyNeural",
    "vi-male": "vi-VN-NamMinhNeural",
    "en-female": "en-US-AriaNeural",
    "en-male": "en-US-GuyNeural",
}


# ---------------------------------------------------------------------------
# Core async implementation
# ---------------------------------------------------------------------------


class TTSResult:
    """Container returned after TTS conversion."""

    def __init__(self, audio_path: Path, word_boundaries: list[dict]):
        self.audio_path = audio_path
        # Each entry: {"text": str, "offset_ms": float, "duration_ms": float}
        self.word_boundaries = word_boundaries

    def __repr__(self) -> str:
        return (
            f"TTSResult(audio={self.audio_path}, "
            f"words={len(self.word_boundaries)})"
        )


async def _convert_chunk(
    text: str,
    voice: str,
    rate: str,
    volume: str,
) -> tuple[bytes, list[dict]]:
    """Convert a single text chunk to audio bytes and timing boundaries.

    edge-tts returns either ``WordBoundary`` or ``SentenceBoundary`` events
    depending on the voice/language.  We collect whichever is available;
    callers can use the ``boundary_type`` key to adapt downstream processing.
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    audio_data = bytearray()
    boundaries: list[dict] = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
            # Offsets are in 100-nanosecond units → convert to ms
            boundaries.append(
                {
                    "text": chunk["text"],
                    "offset_ms": chunk["offset"] / 10_000,
                    "duration_ms": chunk["duration"] / 10_000,
                    "boundary_type": chunk["type"],
                }
            )

    return bytes(audio_data), boundaries


async def _combine_mp3_chunks(chunks: list[bytes], output_path: Path) -> None:
    """Write multiple raw MP3 byte-streams into one file.

    Simple concatenation works for MP3 because each frame is independent.
    For pristine gapless playback pydub/ffmpeg would be ideal, but the
    plain-concat approach is reliable and dependency-free.
    """
    with output_path.open("wb") as fh:
        for chunk in chunks:
            fh.write(chunk)


async def convert_text_async(
    text: str,
    output_path: str | Path,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    volume: str = "+0%",
) -> TTSResult:
    """Convert *text* to speech and save as MP3 at *output_path*.

    Long texts are split into chunks automatically.  Word-boundary data from
    every chunk is merged with adjusted timestamps so callers can build SRT
    files that span the full audio.

    Args:
        text:        Input text (any length).
        output_path: Destination .mp3 file path.
        voice:       edge-tts voice name.
        rate:        Speech rate offset, e.g. ``"+10%"`` or ``"-5%"``.
        volume:      Volume offset, e.g. ``"+0%"``.

    Returns:
        :class:`TTSResult` with the saved audio path and merged word boundaries.
    """
    output_path = ensure_output_dir(output_path)
    chunks = chunk_text(text)
    total = len(chunks)
    logger.info("Processing %d text chunk(s) …", total)

    all_audio: list[bytes] = []
    all_boundaries: list[dict] = []
    cumulative_offset_ms: float = 0.0

    for idx, chunk in enumerate(chunks, start=1):
        logger.info("  chunk %d/%d (%d chars)", idx, total, len(chunk))
        audio_bytes, boundaries = await _convert_chunk(chunk, voice, rate, volume)

        # Shift boundaries by the cumulative audio duration so far
        for wb in boundaries:
            all_boundaries.append(
                {
                    "text": wb["text"],
                    "offset_ms": wb["offset_ms"] + cumulative_offset_ms,
                    "duration_ms": wb["duration_ms"],
                }
            )

        # Estimate duration of this chunk from the last word boundary end time
        if boundaries:
            last = boundaries[-1]
            chunk_duration = last["offset_ms"] + last["duration_ms"]
        else:
            # Rough fallback: ~150 words/min average reading speed
            word_count = len(chunk.split())
            chunk_duration = (word_count / 150) * 60 * 1000

        cumulative_offset_ms += chunk_duration
        all_audio.append(audio_bytes)

    await _combine_mp3_chunks(all_audio, output_path)
    logger.info("Audio saved → %s", output_path)
    return TTSResult(audio_path=output_path, word_boundaries=all_boundaries)


# ---------------------------------------------------------------------------
# Public synchronous wrapper
# ---------------------------------------------------------------------------


def convert_text(
    text: str,
    output_path: str | Path,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    volume: str = "+0%",
) -> TTSResult:
    """Synchronous wrapper around :func:`convert_text_async`."""
    return asyncio.run(
        convert_text_async(text, output_path, voice=voice, rate=rate, volume=volume)
    )


# ---------------------------------------------------------------------------
# Voice listing utility
# ---------------------------------------------------------------------------


async def _list_vi_voices_async() -> list[dict]:
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith("vi")]


def list_vietnamese_voices() -> list[dict]:
    """Return all Vietnamese voices available in edge-tts."""
    return asyncio.run(_list_vi_voices_async())
