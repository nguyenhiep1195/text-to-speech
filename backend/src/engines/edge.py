"""edge-tts engine — Microsoft Edge neural voices (online)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import edge_tts

from ..utils import chunk_text, ensure_output_dir
from .base import BaseTTSEngine, EngineResult

logger = logging.getLogger(__name__)

_LANG_TO_DEFAULT_VOICE = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-AriaNeural",
}


def _speed_to_rate(speed: float) -> str:
    pct = round((speed - 1.0) * 100)
    return f"{pct:+d}%"


class EdgeTTSEngine(BaseTTSEngine):
    name = "edge-tts"

    def convert(
        self,
        text: str,
        output_path: Path,
        *,
        lang: str = "vi",
        speed: float = 1.0,
        voice: str | None = None,
        rate: str | None = None,
        pitch: str = "+0Hz",
        volume: str = "+0%",
        **kwargs,
    ) -> EngineResult:
        resolved_voice = voice or _LANG_TO_DEFAULT_VOICE.get(lang, "vi-VN-HoaiMyNeural")
        resolved_rate = rate if rate is not None else _speed_to_rate(speed)
        return asyncio.run(
            self._convert_async(text, output_path, resolved_voice, resolved_rate, pitch, volume)
        )

    # ------------------------------------------------------------------
    # Async internals
    # ------------------------------------------------------------------

    async def _convert_async(
        self,
        text: str,
        output_path: Path,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
    ) -> EngineResult:
        output_path = ensure_output_dir(output_path)
        chunks = chunk_text(text)
        logger.info("[edge-tts] %d chunk(s) | voice=%s rate=%s pitch=%s", len(chunks), voice, rate, pitch)

        all_audio: list[bytes] = []
        all_boundaries: list[dict] = []
        cumulative_ms: float = 0.0

        for idx, chunk in enumerate(chunks, 1):
            logger.info("  chunk %d/%d (%d chars)", idx, len(chunks), len(chunk))
            audio_bytes, boundaries = await self._convert_chunk(chunk, voice, rate, pitch, volume)

            for b in boundaries:
                all_boundaries.append({
                    "text": b["text"],
                    "offset_ms": b["offset_ms"] + cumulative_ms,
                    "duration_ms": b["duration_ms"],
                    "boundary_type": b["boundary_type"],
                })

            if boundaries:
                last = boundaries[-1]
                cumulative_ms += last["offset_ms"] + last["duration_ms"]
            else:
                cumulative_ms += (len(chunk.split()) / 150) * 60_000

            all_audio.append(audio_bytes)

        with output_path.open("wb") as fh:
            for chunk_bytes in all_audio:
                fh.write(chunk_bytes)

        logger.info("[edge-tts] saved → %s", output_path)
        return EngineResult(audio_path=output_path, boundaries=all_boundaries)

    @staticmethod
    async def _convert_chunk(
        text: str, voice: str, rate: str, pitch: str, volume: str
    ) -> tuple[bytes, list[dict]]:
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
        audio_data = bytearray()
        boundaries: list[dict] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                boundaries.append({
                    "text": chunk["text"],
                    "offset_ms": chunk["offset"] / 10_000,
                    "duration_ms": chunk["duration"] / 10_000,
                    "boundary_type": chunk["type"],
                })
        return bytes(audio_data), boundaries
