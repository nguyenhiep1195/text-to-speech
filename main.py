#!/usr/bin/env python3
"""Entry point for the Text-to-Speech CLI tool.

Usage:
    python main.py --input public/sample.txt --voice vi-female-story --srt
    python main.py --input public/sample.txt --engine gtts --speed 1.5
    python main.py --input public/story_en.txt --engine kokoro --lang en
    python main.py --list-voices
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    from src.cli import build_parser, resolve_args
    from src.tts import convert_text, list_vietnamese_voices, list_presets
    from src.srt import generate_srt_file
    from src.utils import read_text_file
    from src.engines import ENGINES

    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    log = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # --list-voices
    # ------------------------------------------------------------------
    if args.list_voices:
        list_presets()
        print("Raw Vietnamese voices (edge-tts):")
        try:
            voices = list_vietnamese_voices()
            print(f"  {'Name':<30} {'Gender':<8} Locale")
            print("  " + "─" * 50)
            for v in voices:
                print(f"  {v['ShortName']:<30} {v['Gender']:<8} {v['Locale']}")
        except Exception as exc:
            log.error("Could not fetch voice list: %s", exc)
        print(f"\nAvailable engines: {', '.join(ENGINES)}\n")
        return 0

    # ------------------------------------------------------------------
    # Validate & resolve args
    # ------------------------------------------------------------------
    if args.input is None:
        parser.error("the following arguments are required: --input/-i")

    try:
        args = resolve_args(args)
    except ValueError as exc:
        parser.error(str(exc))

    input_path  = Path(args.input)
    output_path = Path(args.output)

    # Build a concise summary line for the log
    if args.engine == "edge-tts":
        params = (f"voice={args.voice} | rate={args.rate} | "
                  f"pitch={args.pitch} | vol={args.volume}")
    else:
        speed_str = f"{args.speed}x" if args.speed else "1.0x"
        params = f"lang={args.lang} | speed={speed_str}"

    log.info("Engine : %s", args.engine)
    log.info("Input  : %s", input_path)
    log.info("Output : %s", output_path)
    log.info("Params : %s", params)
    if args.srt:
        log.info("SRT    : %s", args.srt_output)

    # ------------------------------------------------------------------
    # Read input text
    # ------------------------------------------------------------------
    try:
        text = read_text_file(input_path)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return 2
    except ValueError as exc:
        log.error("%s", exc)
        return 3

    log.info("Loaded %d characters from '%s'", len(text), input_path)

    # ------------------------------------------------------------------
    # TTS conversion
    # ------------------------------------------------------------------
    try:
        result = convert_text(
            text,
            output_path,
            engine_name=args.engine,
            # edge-tts params
            voice=getattr(args, "voice", "vi-VN-HoaiMyNeural"),
            rate=getattr(args, "rate", "+0%"),
            pitch=getattr(args, "pitch", "+0Hz"),
            volume=getattr(args, "volume", "+0%"),
            # common params
            lang=args.lang,
            speed=args.speed or 1.0,
        )
    except ImportError as exc:
        log.error("%s", exc)
        return 4
    except Exception as exc:
        log.error("TTS conversion failed: %s", exc)
        if args.verbose:
            log.exception("Traceback:")
        return 4

    print(f"\n✓  Audio saved  →  {result.audio_path}")

    # ------------------------------------------------------------------
    # SRT generation (edge-tts only)
    # ------------------------------------------------------------------
    if args.srt:
        if args.engine != "edge-tts":
            log.warning(
                "SRT generation is only supported with --engine edge-tts. "
                "Skipping."
            )
        elif not result.boundaries:
            log.warning("No timing data from TTS engine — skipping SRT.")
        else:
            try:
                srt_path = generate_srt_file(
                    result.boundaries,
                    srt_path=args.srt_output,
                    words_per_cue=args.words_per_cue,
                )
                print(f"✓  SRT saved    →  {srt_path}")
            except Exception as exc:
                log.error("SRT generation failed: %s", exc)
                return 5

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
