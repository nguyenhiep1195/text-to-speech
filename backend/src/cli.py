"""CLI argument parser for the TTS tool."""

from __future__ import annotations

import argparse
from pathlib import Path

from .engines import DEFAULT_ENGINE, ENGINES
from .tts import DEFAULT_PRESET, VOICE_PRESETS


def build_parser() -> argparse.ArgumentParser:
    engine_choices = list(ENGINES)
    preset_names = ", ".join(VOICE_PRESETS)

    parser = argparse.ArgumentParser(
        prog="python main.py",
        description=(
            "Text-to-Speech CLI — converts .txt files to .mp3/.wav audio "
            "with optional .srt subtitle generation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_epilog(),
    )

    # --- Input / Output ---
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
            "Path for the output audio file. "
            "Defaults to output/<input_stem>.mp3 (or .wav for kokoro)."
        ),
    )

    # --- Engine ---
    parser.add_argument(
        "--engine",
        default=DEFAULT_ENGINE,
        choices=engine_choices,
        metavar="ENGINE",
        help=(
            f"TTS engine to use. Choices: {', '.join(engine_choices)}. "
            f"Default: {DEFAULT_ENGINE}. "
            "edge-tts=online/Microsoft, gtts=online/Google, kokoro=offline/neural"
        ),
    )
    parser.add_argument(
        "--lang",
        default="vi",
        metavar="LANG",
        help=(
            "Language code for gtts/kokoro engines (ISO 639-1). "
            "Examples: vi, en, fr, ja. Default: vi. "
            "Note: kokoro does not support Vietnamese — falls back to English."
        ),
    )

    # --- Subtitle ---
    parser.add_argument(
        "--srt",
        action="store_true",
        default=False,
        help="Generate a .srt subtitle file (edge-tts only).",
    )
    parser.add_argument(
        "--srt-output",
        default=None,
        metavar="FILE",
        help="Custom path for the .srt file.",
    )
    parser.add_argument(
        "--words-per-cue",
        type=int,
        default=8,
        metavar="N",
        help="Words per SRT subtitle cue (default: 8).",
    )

    # --- edge-tts specific ---
    edge_group = parser.add_argument_group(
        "edge-tts options",
        "These options apply only when --engine edge-tts (default).",
    )
    edge_group.add_argument(
        "--voice",
        default=DEFAULT_PRESET,
        metavar="VOICE",
        help=(
            f"Preset shortcut or full edge-tts voice name. "
            f"Presets: {preset_names}."
        ),
    )
    edge_group.add_argument(
        "--pitch",
        default="-10Hz",
        metavar="PITCH",
        help='Pitch offset, e.g. "-20Hz" or "+15Hz". Overrides preset. Default: -10Hz.',
    )
    edge_group.add_argument(
        "--volume",
        default="+0%",
        metavar="VOL",
        help='Volume offset, e.g. "+10%%". Default: +0%%.',
    )

    # --- Common voice params ---
    parser.add_argument(
        "--speed",
        type=float,
        default=1.6,
        metavar="SPEED",
        help=(
            "Speed multiplier 0.5–2.0 (1.0=normal, 2.0=double speed). "
            "For edge-tts, overrides --rate. "
            "For gtts, values < 0.9 enable slow mode. Default: 1.6."
        ),
    )
    parser.add_argument(
        "--rate",
        default=None,
        metavar="RATE",
        help=(
            'edge-tts rate offset, e.g. "+10%%" or "-5%%". '
            "Ignored when --speed is set."
        ),
    )

    # --- Misc ---
    parser.add_argument(
        "--list-voices",
        action="store_true",
        default=False,
        help="List edge-tts presets and Vietnamese voices, then exit.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging.",
    )

    return parser


def _build_epilog() -> str:
    lines = [
        "  # edge-tts (default) — giọng truyện nữ",
        "  python main.py --input public/sample.txt --voice vi-female-story --srt",
        "",
        "  # gTTS — Google, tốc độ 1.5x",
        "  python main.py --input public/sample.txt --engine gtts --speed 1.5",
        "",
        "  # Kokoro — offline, tiếng Anh",
        "  python main.py --input public/story_en.txt --engine kokoro --lang en",
        "",
        "  # Xem preset",
        "  python main.py --list-voices",
    ]
    return "Examples:\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _speed_to_rate(speed: float) -> str:
    pct = round((speed - 1.0) * 100)
    return f"{pct:+d}%"


def resolve_args(args: argparse.Namespace) -> argparse.Namespace:
    """Resolve preset shortcuts and fill in defaults."""

    # Validate speed range
    if args.speed is not None and not (0.5 <= args.speed <= 2.0):
        raise ValueError(f"--speed must be between 0.5 and 2.0 (got {args.speed})")

    # --- edge-tts voice/rate/pitch resolution ---
    if args.engine == "edge-tts":
        preset = VOICE_PRESETS.get(args.voice)
        if preset:
            resolved_voice = preset.voice
            if args.speed is not None:
                resolved_rate = _speed_to_rate(args.speed)
            elif args.rate is not None:
                resolved_rate = args.rate
            else:
                resolved_rate = preset.rate
            resolved_pitch = args.pitch if args.pitch is not None else preset.pitch
        else:
            resolved_voice = args.voice
            resolved_rate = (
                _speed_to_rate(args.speed) if args.speed is not None
                else args.rate if args.rate is not None
                else "+0%"
            )
            resolved_pitch = args.pitch if args.pitch is not None else "+0Hz"

        args.voice = resolved_voice
        args.rate  = resolved_rate
        args.pitch = resolved_pitch

    # --- Default output path ---
    if args.output is None:
        stem = Path(args.input).stem
        ext = ".wav" if args.engine == "kokoro" else ".mp3"
        args.output = str(Path("output") / f"{stem}{ext}")

    # --- Default SRT path ---
    if args.srt and args.srt_output is None:
        args.srt_output = str(Path(args.output).with_suffix(".srt"))

    return args
