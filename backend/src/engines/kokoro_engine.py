"""Kokoro TTS engine — offline neural TTS (hexgrad/Kokoro-82M).

Kokoro is a lightweight (~82 MB) open-source neural TTS model that runs
fully offline.  It produces very natural-sounding English speech and
several other languages, but **does not natively support Vietnamese**.

Supported lang codes
--------------------
  a  → American English   b  → British English
  e  → Spanish            f  → French
  h  → Hindi              i  → Italian
  j  → Japanese           k  → Korean
  p  → Portuguese         z  → Mandarin Chinese

For Vietnamese text use ``--engine edge-tts`` or ``--engine gtts``.

Install
-------
  pip install kokoro soundfile

On first run Kokoro automatically downloads the model weights (~82 MB)
from HuggingFace Hub (requires internet for the initial download only).
Subsequent runs work fully offline.

Voice names (English)
---------------------
  Female: af_bella, af_sarah, af_nicole, af_sky
  Male  : am_adam, am_michael, bm_george (British)
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..utils import chunk_text, ensure_output_dir
from .base import BaseTTSEngine, EngineResult

logger = logging.getLogger(__name__)

_SAMPLE_RATE = 24_000  # Kokoro always outputs 24 kHz audio

# Maps our ISO 639-1 lang codes to Kokoro single-letter lang codes
_LANG_MAP: dict[str, str] = {
    "en": "a",    # American English (default fallback)
    "en-us": "a",
    "en-gb": "b",
    "es": "e",
    "fr": "f",
    "hi": "h",
    "it": "i",
    "ja": "j",
    "ko": "k",
    "pt": "p",
    "zh": "z",
}

_DEFAULT_VOICE = "af_bella"


def _import_kokoro():
    try:
        from kokoro import KPipeline
        return KPipeline
    except ImportError:
        raise ImportError(
            "kokoro is not installed.\n"
            "Run:  pip install kokoro soundfile\n"
            "Note: ~82 MB model is downloaded automatically on first use."
        )


def _import_soundfile():
    try:
        import soundfile as sf
        return sf
    except ImportError:
        raise ImportError(
            "soundfile is not installed.  Run:  pip install soundfile"
        )


def _import_numpy():
    try:
        import numpy as np
        return np
    except ImportError:
        raise ImportError(
            "numpy is not installed.  Run:  pip install numpy"
        )


class KokoroEngine(BaseTTSEngine):
    name = "kokoro"

    def convert(
        self,
        text: str,
        output_path: Path,
        *,
        lang: str = "en",
        speed: float = 1.0,
        voice: str | None = None,
        **kwargs,
    ) -> EngineResult:
        KPipeline = _import_kokoro()
        sf = _import_soundfile()
        np = _import_numpy()

        if lang == "vi":
            logger.warning(
                "[kokoro] Vietnamese is not supported by Kokoro. "
                "Falling back to American English (lang='a'). "
                "Use --engine edge-tts or --engine gtts for Vietnamese."
            )
            lang = "en"

        lang_code = _LANG_MAP.get(lang.lower(), "a")
        resolved_voice = voice or _DEFAULT_VOICE

        # Kokoro output is always WAV; change extension accordingly
        output_path = ensure_output_dir(output_path.with_suffix(".wav"))

        chunks = chunk_text(text)
        logger.info(
            "[kokoro] %d chunk(s) | lang=%s (%s) voice=%s speed=%.2f",
            len(chunks), lang, lang_code, resolved_voice, speed,
        )

        all_samples: list[np.ndarray] = []
        pipeline = KPipeline(lang_code=lang_code)

        for idx, chunk in enumerate(chunks, 1):
            logger.info("  chunk %d/%d (%d chars)", idx, len(chunks), len(chunk))
            chunk_samples: list[np.ndarray] = []
            for _, _, audio in pipeline(chunk, voice=resolved_voice, speed=speed):
                chunk_samples.append(audio)
            if chunk_samples:
                all_samples.append(np.concatenate(chunk_samples))

        if not all_samples:
            raise RuntimeError("[kokoro] No audio generated — check input text.")

        audio = np.concatenate(all_samples)
        sf.write(str(output_path), audio, _SAMPLE_RATE)

        logger.info("[kokoro] saved → %s  (WAV, 24 kHz)", output_path)
        logger.info(
            "[kokoro] Note: Kokoro outputs WAV files. "
            "SRT generation is not available for this engine."
        )
        return EngineResult(audio_path=output_path, boundaries=[])
