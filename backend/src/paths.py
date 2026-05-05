"""Project directory layout for the TTS CLI."""

from __future__ import annotations

from pathlib import Path

# text-to-speech/ (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

AUDIO_FILENAME_MP3 = "audio.mp3"
