"""SRT subtitle file generation from edge-tts boundary data.

edge-tts may return either ``WordBoundary`` (word-level) or
``SentenceBoundary`` (sentence-level) events.  Both are handled:

* **WordBoundary** — boundaries are grouped into cues of *words_per_cue* words.
* **SentenceBoundary** — each sentence is split into word groups; timing is
  distributed proportionally by character count so subtitles remain readable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from .utils import format_duration

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class SRTCue:
    """A single SRT subtitle entry."""

    index: int
    start_ms: float
    end_ms: float
    text: str

    def __str__(self) -> str:
        return (
            f"{self.index}\n"
            f"{format_duration(self.start_ms)} --> {format_duration(self.end_ms)}\n"
            f"{self.text}\n"
        )


@dataclass
class SRTDocument:
    """Ordered collection of :class:`SRTCue` entries."""

    cues: list[SRTCue] = field(default_factory=list)

    def add_cue(self, start_ms: float, end_ms: float, text: str) -> None:
        self.cues.append(
            SRTCue(
                index=len(self.cues) + 1,
                start_ms=start_ms,
                end_ms=end_ms,
                text=text,
            )
        )

    def to_string(self) -> str:
        return "\n".join(str(cue) for cue in self.cues)

    def save(self, path: str | Path) -> Path:
        srt_path = Path(path)
        srt_path.parent.mkdir(parents=True, exist_ok=True)
        srt_path.write_text(self.to_string(), encoding="utf-8")
        logger.info("SRT saved → %s", srt_path)
        return srt_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _expand_sentence_to_word_boundaries(
    sentence_text: str,
    sentence_offset_ms: float,
    sentence_duration_ms: float,
    gap_ms: float = 50,
) -> list[dict]:
    """Break a sentence boundary into per-word boundaries with proportional timing.

    Timing is allocated proportionally to each word's character length relative
    to the total character length of the sentence (excluding spaces), giving a
    natural feel even without true word-level data.
    """
    words = sentence_text.split()
    if not words:
        return []

    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        total_chars = len(words)

    usable_duration = max(0.0, sentence_duration_ms - gap_ms)
    result: list[dict] = []
    cursor_ms = sentence_offset_ms

    for word in words:
        proportion = len(word) / total_chars
        word_duration = usable_duration * proportion
        result.append(
            {
                "text": word,
                "offset_ms": cursor_ms,
                "duration_ms": word_duration,
                "boundary_type": "WordBoundary",
            }
        )
        cursor_ms += word_duration

    return result


def _normalise_to_word_boundaries(boundaries: list[dict]) -> list[dict]:
    """Convert a mixed boundary list to word-level entries.

    Sentence boundaries are expanded; word boundaries are passed through.
    """
    result: list[dict] = []
    for b in boundaries:
        if b.get("boundary_type") == "SentenceBoundary":
            result.extend(
                _expand_sentence_to_word_boundaries(
                    b["text"], b["offset_ms"], b["duration_ms"]
                )
            )
        else:
            result.append(b)
    return result


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_srt(
    boundaries: list[dict],
    words_per_cue: int = 8,
    max_cue_duration_ms: float = 5_000,
    min_cue_duration_ms: float = 500,
    gap_between_cues_ms: float = 50,
) -> SRTDocument:
    """Build an :class:`SRTDocument` from edge-tts boundary data.

    Accepts both word-level and sentence-level boundaries (or a mix).
    Sentence boundaries are automatically expanded to word-level timing.

    Args:
        boundaries:          List of dicts with keys ``text``, ``offset_ms``,
                             ``duration_ms``, ``boundary_type``.
        words_per_cue:       Maximum words grouped into one subtitle cue.
        max_cue_duration_ms: Force a cue break when accumulated time exceeds
                             this value (ms).
        min_cue_duration_ms: Minimum display duration per cue (ms).
        gap_between_cues_ms: Small gap between consecutive cues (ms).

    Returns:
        A populated :class:`SRTDocument`.
    """
    if not boundaries:
        logger.warning("No boundaries provided — SRT will be empty.")
        return SRTDocument()

    word_boundaries = _normalise_to_word_boundaries(boundaries)
    if not word_boundaries:
        return SRTDocument()

    doc = SRTDocument()
    buffer_words: list[str] = []
    cue_start_ms: float = word_boundaries[0]["offset_ms"]
    cue_end_ms: float = cue_start_ms

    def _flush(forced_end_ms: float | None = None) -> None:
        nonlocal buffer_words, cue_start_ms, cue_end_ms
        if not buffer_words:
            return
        end = forced_end_ms if forced_end_ms is not None else cue_end_ms
        end = max(end, cue_start_ms + min_cue_duration_ms)
        doc.add_cue(
            start_ms=cue_start_ms,
            end_ms=end,
            text=" ".join(buffer_words),
        )
        buffer_words.clear()

    for wb in word_boundaries:
        word_end = wb["offset_ms"] + wb["duration_ms"]
        duration_so_far = word_end - cue_start_ms

        should_break = (
            len(buffer_words) >= words_per_cue
            or duration_so_far > max_cue_duration_ms
        )

        if should_break and buffer_words:
            _flush(forced_end_ms=wb["offset_ms"] - gap_between_cues_ms)
            cue_start_ms = wb["offset_ms"]

        buffer_words.append(wb["text"])
        cue_end_ms = word_end

    _flush()

    logger.debug(
        "Generated %d SRT cues from %d boundaries",
        len(doc.cues),
        len(boundaries),
    )
    return doc


# ---------------------------------------------------------------------------
# High-level helper
# ---------------------------------------------------------------------------


def generate_srt_file(
    boundaries: list[dict],
    srt_path: str | Path,
    words_per_cue: int = 8,
) -> Path:
    """Build and save an SRT file in one call.

    Args:
        boundaries:   Boundary data from :class:`~src.tts.TTSResult`.
        srt_path:     Destination path for the ``.srt`` file.
        words_per_cue: Words grouped per subtitle cue.

    Returns:
        The :class:`~pathlib.Path` of the saved SRT file.
    """
    doc = build_srt(boundaries, words_per_cue=words_per_cue)
    return doc.save(srt_path)
