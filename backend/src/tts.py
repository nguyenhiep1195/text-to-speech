"""Top-level TTS facade.

Exposes:
- ``VOICE_PRESETS``  — edge-tts voice presets (rate + pitch combinations)
- ``convert_text()`` — dispatch to any registered engine
- ``TTSResult``      — alias kept for backward compatibility
- ``list_presets()`` / ``list_vietnamese_voices()`` — info helpers
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import edge_tts

from .engines import DEFAULT_ENGINE, EngineResult, get_engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backward-compat alias
# ---------------------------------------------------------------------------

TTSResult = EngineResult


# ---------------------------------------------------------------------------
# Voice presets (edge-tts only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VoicePreset:
    voice: str
    rate: str
    pitch: str
    desc: str


# fmt: off
VOICE_PRESETS: dict[str, VoicePreset] = {
    # ── Vietnamese Female ────────────────────────────────────────────────────
    "vi-female":            VoicePreset("vi-VN-HoaiMyNeural",  "+0%",  "+0Hz",  "Nữ · giọng chuẩn"),
    "vi-female-slow":       VoicePreset("vi-VN-HoaiMyNeural",  "-15%", "+0Hz",  "Nữ · chậm rãi, rõ ràng"),
    "vi-female-gentle":     VoicePreset("vi-VN-HoaiMyNeural",  "-10%", "+25Hz", "Nữ · nhẹ nhàng, cao giọng"),
    "vi-female-news":       VoicePreset("vi-VN-HoaiMyNeural",  "+8%",  "-15Hz", "Nữ · giọng đọc tin tức"),
    "vi-female-fast":       VoicePreset("vi-VN-HoaiMyNeural",  "+20%", "+0Hz",  "Nữ · nhanh"),
    "vi-female-story":      VoicePreset("vi-VN-HoaiMyNeural",  "-12%", "+15Hz", "Nữ · đọc truyện, ấm áp, tình cảm"),
    "vi-female-story-warm": VoicePreset("vi-VN-HoaiMyNeural",  "-18%", "+30Hz", "Nữ · đọc truyện, chậm rãi, sâu lắng"),
    # ── Vietnamese Male ──────────────────────────────────────────────────────
    "vi-male":              VoicePreset("vi-VN-NamMinhNeural", "+0%",  "+0Hz",  "Nam · giọng chuẩn"),
    "vi-male-deep":         VoicePreset("vi-VN-NamMinhNeural", "-8%",  "-30Hz", "Nam · trầm ấm"),
    "vi-male-narrator":     VoicePreset("vi-VN-NamMinhNeural", "-12%", "+0Hz",  "Nam · thuyết minh"),
    "vi-male-fast":         VoicePreset("vi-VN-NamMinhNeural", "+20%", "+0Hz",  "Nam · nhanh"),
    "vi-male-story":        VoicePreset("vi-VN-NamMinhNeural", "-15%", "-20Hz", "Nam · đọc truyện, trầm lắng, cuốn hút"),
    "vi-male-story-epic":   VoicePreset("vi-VN-NamMinhNeural", "-20%", "-40Hz", "Nam · đọc truyện sử thi, rất trầm hùng"),
    # ── English ─────────────────────────────────────────────────────────────
    "en-female":            VoicePreset("en-US-AriaNeural",    "+0%",  "+0Hz",  "English female"),
    "en-male":              VoicePreset("en-US-GuyNeural",     "+0%",  "+0Hz",  "English male"),
}
# fmt: on

DEFAULT_PRESET = "vi-female"
DEFAULT_VOICE = VOICE_PRESETS[DEFAULT_PRESET].voice


# ---------------------------------------------------------------------------
# Unified convert entry point
# ---------------------------------------------------------------------------


def convert_text(
    text: str,
    output_path: str | Path,
    *,
    engine_name: str = DEFAULT_ENGINE,
    # edge-tts params
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    ssml_mode: bool = False,
    # common params
    lang: str = "vi",
    speed: float = 1.0,
    write_audio: bool = True,
) -> EngineResult:
    """Convert *text* to speech using the chosen engine.

    Args:
        text:         Input text.
        output_path:  Destination audio file path.
        engine_name:  One of ``"edge-tts"``, ``"gtts"``.
        voice:        edge-tts voice name (edge-tts only).
        rate:         Rate offset string, e.g. ``"+10%"`` (edge-tts only).
        pitch:        Pitch offset, e.g. ``"-20Hz"`` (edge-tts only).
        volume:       Volume offset (edge-tts only).
        lang:         ISO 639-1 language code for gtts (``"vi"``, ``"en"`` …).
        speed:        Speed multiplier 0.5–2.0 (gtts; edge-tts uses rate).
        write_audio:  If False (edge-tts only), skip writing MP3 but still run
                      synthesis to collect word-boundary timings for SRT.

    Returns:
        :class:`EngineResult` with audio path and timing boundaries (if available).
    """
    engine = get_engine(engine_name)
    return engine.convert(
        text,
        Path(output_path),
        lang=lang,
        speed=speed,
        # edge-tts specific — ignored by other engines
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
        ssml_mode=ssml_mode,
        write_audio=write_audio,
    )


# ---------------------------------------------------------------------------
# Info helpers
# ---------------------------------------------------------------------------


async def _list_vi_voices_async() -> list[dict]:
    voices = await edge_tts.list_voices()
    return [v for v in voices if v["Locale"].startswith("vi")]


def list_vietnamese_voices() -> list[dict]:
    """Return raw Vietnamese voices available in edge-tts."""
    return asyncio.run(_list_vi_voices_async())


def list_presets() -> None:
    """Print the full edge-tts preset table to stdout."""
    col = 22
    print(f"\n{'Shortcut':<{col}} {'Voice':<26} {'Rate':<7} {'Pitch':<8} Description")
    print("─" * 84)
    for name, p in VOICE_PRESETS.items():
        print(f"{name:<{col}} {p.voice:<26} {p.rate:<7} {p.pitch:<8} {p.desc}")
    print()
