"""CLI argument parser for the TTS tool."""

from __future__ import annotations

import argparse
from pathlib import Path

from .tts import AVAILABLE_VOICES, DEFAULT_VOICE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description=(
            "Text-to-Speech CLI — converts .txt files to .mp3 audio "
            "with optional .srt subtitle generation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_epilog(),
    )

    # --- Required / primary args ---
    parser.add_argument(
        "--input", "-i",
        required=False,
        default=None,
        metavar="FILE",
        help="Path to the input .txt file (e.g. public/sample.txt).",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help=(
            "Path for the output .mp3 file (e.g. output/audio.mp3). "
            "Defaults to output/<input_stem>.mp3."
        ),
    )

    # --- Subtitle ---
    parser.add_argument(
        "--srt",
        action="store_true",
        default=False,
        help="Generate a .srt subtitle file alongside the audio.",
    )
    parser.add_argument(
        "--srt-output",
        default=None,
        metavar="FILE",
        help=(
            "Custom path for the .srt file. "
            "Defaults to the same path as --output with .srt extension."
        ),
    )
    parser.add_argument(
        "--words-per-cue",
        type=int,
        default=8,
        metavar="N",
        help="Number of words per SRT subtitle cue (default: 8).",
    )

    # --- Voice / language ---
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        metavar="VOICE",
        help=(
            f"edge-tts voice name or shortcut. "
            f"Shortcuts: {', '.join(AVAILABLE_VOICES)}. "
            f"Default: {DEFAULT_VOICE}"
        ),
    )
    parser.add_argument(
        "--rate",
        default="+0%",
        metavar="RATE",
        help='Speech rate offset, e.g. "+10%%" or "-5%%". Default: +0%%.',
    )
    parser.add_argument(
        "--volume",
        default="+0%",
        metavar="VOL",
        help='Volume offset, e.g. "+10%%" or "-5%%". Default: +0%%.',
    )

    # --- Misc ---
    parser.add_argument(
        "--list-voices",
        action="store_true",
        default=False,
        help="List available Vietnamese voices and exit.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging.",
    )

    return parser


def _build_epilog() -> str:
    examples = [
        "  # Basic conversion",
        "  python main.py --input public/sample.txt",
        "",
        "  # Custom output path",
        "  python main.py --input public/sample.txt --output output/audio.mp3",
        "",
        "  # With SRT subtitles",
        "  python main.py --input public/sample.txt --output output/audio.mp3 --srt",
        "",
        "  # Male voice, faster rate",
        "  python main.py --input public/sample.txt --voice vi-VN-NamMinhNeural --rate +15%",
        "",
        "  # List Vietnamese voices",
        "  python main.py --list-voices",
    ]
    return "Examples:\n" + "\n".join(examples)


def resolve_args(args: argparse.Namespace) -> argparse.Namespace:
    """Post-process parsed arguments: resolve shortcuts and default paths."""
    # Resolve voice shortcut → full voice name
    args.voice = AVAILABLE_VOICES.get(args.voice, args.voice)

    # Default output path
    if args.output is None:
        input_stem = Path(args.input).stem
        args.output = str(Path("output") / f"{input_stem}.mp3")

    # Default SRT path: same as output but .srt extension
    if args.srt and args.srt_output is None:
        args.srt_output = str(Path(args.output).with_suffix(".srt"))

    return args
