"""CLI argument parser for the TTS tool."""

from __future__ import annotations

import argparse
from pathlib import Path

from .engines import DEFAULT_ENGINE, ENGINES
from .paths import AUDIO_FILENAME_MP3, INPUT_DIR, OUTPUT_DIR
from .tts import DEFAULT_PRESET, VOICE_PRESETS


def build_parser() -> argparse.ArgumentParser:
    engine_choices = list(ENGINES)
    preset_names = ", ".join(VOICE_PRESETS)

    parser = argparse.ArgumentParser(
        prog="python main.py",
        description=(
            "Text-to-Speech CLI — reads .txt from the input/ folder, writes "
            "output/<tên-file>/audio.mp3, optional .srt."
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
        help=(
            "Input .txt: filename inside input/ (e.g. story.txt) or any path. "
            "If omitted, all *.txt files in input/ are converted."
        ),
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        metavar="FILE",
        help=(
            "Output audio path (overrides default layout). "
            f"Default: output/<stem>/{AUDIO_FILENAME_MP3}."
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
            "edge-tts=online/Microsoft, gtts=online/Google"
        ),
    )
    parser.add_argument(
        "--lang",
        default="vi",
        metavar="LANG",
        help=(
            "Language code for gtts engine (ISO 639-1). "
            "Examples: vi, en, fr, ja. Default: vi."
        ),
    )

    # --- Subtitle ---
    parser.add_argument(
        "--srt-only",
        action="store_true",
        default=False,
        help=(
            "Only write the .srt file (implies --srt); do not save MP3. "
            "Requires --engine edge-tts. Still calls the API to obtain timings."
        ),
    )
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
        default=1.35,
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

    # --- AI SSML ---
    ai_group = parser.add_argument_group(
        "AI SSML options",
        "Use AI (Gemini/ChatGPT) to generate natural SSML before TTS synthesis.",
    )
    ai_group.add_argument(
        "--ai-ssml",
        action="store_true",
        default=False,
        help=(
            "Use AI to convert input text to SSML first, then synthesize with edge-tts. "
            "Choose provider with --ai-provider (default: gemini)."
        ),
    )
    ai_group.add_argument(
        "--ai-provider",
        default="gemini",
        choices=["gemini", "openai"],
        metavar="PROVIDER",
        help=(
            "AI provider for SSML generation: gemini (free, default) or openai (paid). "
        ),
    )
    ai_group.add_argument(
        "--gemini-key",
        default=None,
        metavar="KEY",
        help=(
            "Google Gemini API key (overrides GEMINI_API_KEY env var). "
            "Get a free key at https://aistudio.google.com/apikey"
        ),
    )
    ai_group.add_argument(
        "--gemini-model",
        default="gemini-2.0-flash",
        metavar="MODEL",
        help="Gemini model to use (default: gemini-2.0-flash).",
    )
    ai_group.add_argument(
        "--openai-key",
        default=None,
        metavar="KEY",
        help="OpenAI API key (overrides OPENAI_API_KEY env var).",
    )
    ai_group.add_argument(
        "--openai-model",
        default="gpt-4o",
        metavar="MODEL",
        help="ChatGPT model to use for SSML generation (default: gpt-4o).",
    )
    ai_group.add_argument(
        "--save-ssml",
        default=None,
        metavar="FILE",
        help=(
            "Save generated SSML to this path "
            f"(default: output/<stem>/<stem>.ssml when --ai-ssml is set)."
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
        "  # Chỉ tạo phụ đề .srt (không lưu MP3) — vẫn dùng edge-tts để lấy timing",
        "  python main.py --input sample.txt --voice vi-female-story --srt-only",
        "",
        "  # edge-tts — một file: output/sample/audio.mp3",
        "  python main.py --input sample.txt --voice vi-female-story --srt",
        "",
        "  # Tất cả file *.txt trong input/",
        "  python main.py",
        "",
        "  # gTTS",
        "  python main.py --input sample.txt --engine gtts --speed 1.5",
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

    return args


def resolve_input_path(raw: str, *, input_dir: Path = INPUT_DIR) -> Path:
    """Resolve CLI input to an absolute path.

    Relative paths are tried against the current working directory first;
    if not found, ``input_dir`` is used (so ``story.txt`` → ``input/story.txt``).
    """
    p = Path(raw)
    if p.is_absolute():
        return p.resolve()
    cwd_try = (Path.cwd() / p).resolve()
    if cwd_try.is_file():
        return cwd_try
    return (input_dir / p).resolve()


def collect_input_txt_paths(raw_input: str | None, *, input_dir: Path = INPUT_DIR) -> list[Path]:
    """Return ordered list of .txt files to convert."""
    if raw_input is not None:
        return [resolve_input_path(raw_input, input_dir=input_dir)]
    paths = sorted(input_dir.glob("*.txt"))
    return paths


def apply_output_paths_for_input(
    args: argparse.Namespace,
    input_path: Path,
    *,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Set ``args.output``, optional ``args.srt_output`` / ``args.save_ssml`` defaults."""
    if args.output is None:
        stem = input_path.stem
        args.output = str(output_dir / stem / AUDIO_FILENAME_MP3)
    else:
        args.output = str(Path(args.output).expanduser().resolve())

    out_audio = Path(args.output)

    if args.srt and args.srt_output is None:
        args.srt_output = str(out_audio.with_suffix(".srt"))

    if args.ai_ssml and args.save_ssml is None:
        args.save_ssml = str(out_audio.parent / f"{input_path.stem}.ssml")
