"""Utility helpers: file I/O, text chunking, encoding detection."""

from __future__ import annotations

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_ENCODINGS = ("utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252")
MAX_CHUNK_CHARS = 3_000  # edge-tts handles ~5 k chars; keep headroom


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def read_text_file(path: str | Path) -> str:
    """Read a text file, trying several encodings until one succeeds.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when the file is empty or unreadable with known encodings.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a regular file: {file_path}")

    for encoding in SUPPORTED_ENCODINGS:
        try:
            text = file_path.read_text(encoding=encoding)
            text = text.strip()
            if not text:
                raise ValueError(f"Input file is empty: {file_path}")
            return text
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(
        f"Cannot decode '{file_path}'. "
        f"Tried encodings: {', '.join(SUPPORTED_ENCODINGS)}"
    )


def ensure_output_dir(path: str | Path) -> Path:
    """Create parent directories for *path* if they don't exist."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving whitespace within sentences."""
    # Split on sentence-ending punctuation followed by whitespace or EOL.
    # Works well for Vietnamese (. ! ?) and also handles newlines as breaks.
    pattern = r"(?<=[.!?…])\s+|(?<=\n)\s*"
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split *text* into chunks of at most *max_chars* characters.

    Chunks are broken at sentence boundaries when possible; a single sentence
    that exceeds *max_chars* is split at word boundaries instead.
    """
    sentences = _split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence) + 1  # +1 for the joining space

        if sentence_len > max_chars:
            # Flush current buffer first
            if current:
                chunks.append(" ".join(current))
                current, current_len = [], 0
            # Then split the oversized sentence by words
            words = sentence.split()
            word_buf: list[str] = []
            word_len = 0
            for word in words:
                if word_len + len(word) + 1 > max_chars and word_buf:
                    chunks.append(" ".join(word_buf))
                    word_buf, word_len = [], 0
                word_buf.append(word)
                word_len += len(word) + 1
            if word_buf:
                chunks.append(" ".join(word_buf))
        elif current_len + sentence_len > max_chars:
            chunks.append(" ".join(current))
            current, current_len = [sentence], sentence_len
        else:
            current.append(sentence)
            current_len += sentence_len

    if current:
        chunks.append(" ".join(current))

    return chunks


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def format_duration(milliseconds: float) -> str:
    """Return 'HH:MM:SS,mmm' timestamp string used in SRT files."""
    ms = int(milliseconds)
    hours, remainder = divmod(ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
