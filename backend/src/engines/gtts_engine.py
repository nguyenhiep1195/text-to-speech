"""gTTS engine — Google Text-to-Speech (online, free, no API key).

Supports all languages Google Translate supports, including Vietnamese.
Does not provide word-level timing data; SRT output is not available.

Install:  pip install gTTS
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from ..utils import chunk_text, ensure_output_dir
from .base import BaseTTSEngine, EngineResult

logger = logging.getLogger(__name__)


def _import_gtts():
    try:
        from gtts import gTTS
        return gTTS
    except ImportError:
        raise ImportError(
            "gTTS is not installed. Run:  pip install gTTS"
        )


class GTTSEngine(BaseTTSEngine):
    name = "gtts"

    def convert(
        self,
        text: str,
        output_path: Path,
        *,
        lang: str = "vi",
        speed: float = 1.0,
        **kwargs,
    ) -> EngineResult:
        gTTS = _import_gtts()
        output_path = ensure_output_dir(output_path)

        # gTTS speed: only slow=True (≈0.7×) or normal (1.0×)
        slow = speed < 0.9

        chunks = chunk_text(text)
        logger.info("[gtts] %d chunk(s) | lang=%s slow=%s", len(chunks), lang, slow)

        mp3_parts: list[bytes] = []
        for idx, chunk in enumerate(chunks, 1):
            logger.info("  chunk %d/%d (%d chars)", idx, len(chunks), len(chunk))
            buf = BytesIO()
            gTTS(text=chunk, lang=lang, slow=slow).write_to_fp(buf)
            mp3_parts.append(buf.getvalue())

        with output_path.open("wb") as fh:
            for part in mp3_parts:
                fh.write(part)

        logger.info("[gtts] saved → %s", output_path)
        logger.info(
            "[gtts] Note: gTTS does not provide word timestamps — "
            "SRT generation is not available for this engine."
        )
        return EngineResult(audio_path=output_path, boundaries=[])
