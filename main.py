#!/usr/bin/env python3
"""Entry point for the Text-to-Speech CLI tool.

Usage:
    python main.py --input public/sample.txt --output output/audio.mp3 --srt
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
    from src.tts import convert_text, list_vietnamese_voices
    from src.srt import generate_srt_file
    from src.utils import read_text_file

    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    log = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # --list-voices
    # ------------------------------------------------------------------
    if args.list_voices:
        log.info("Fetching available Vietnamese voices …")
        try:
            voices = list_vietnamese_voices()
        except Exception as exc:
            log.error("Failed to fetch voices: %s", exc)
            return 1

        if not voices:
            print("No Vietnamese voices found.")
            return 0

        print(f"\n{'Name':<40} {'Gender':<8} {'Locale'}")
        print("-" * 65)
        for v in voices:
            print(f"{v['ShortName']:<40} {v['Gender']:<8} {v['Locale']}")
        print()
        return 0

    # ------------------------------------------------------------------
    # Resolve paths and defaults
    # ------------------------------------------------------------------
    if args.input is None:
        parser.error("the following arguments are required: --input/-i")

    args = resolve_args(args)

    input_path = Path(args.input)
    output_path = Path(args.output)

    log.info("Input  : %s", input_path)
    log.info("Output : %s", output_path)
    log.info("Voice  : %s", args.voice)
    log.info("Rate   : %s  Volume: %s", args.rate, args.volume)
    if args.srt:
        log.info("SRT    : %s", args.srt_output)

    # ------------------------------------------------------------------
    # Read input
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
            output_path=output_path,
            voice=args.voice,
            rate=args.rate,
            volume=args.volume,
        )
    except Exception as exc:
        log.error("TTS conversion failed: %s", exc)
        if args.verbose:
            log.exception("Traceback:")
        return 4

    print(f"\n✓  Audio saved  →  {result.audio_path}")

    # ------------------------------------------------------------------
    # SRT generation (optional)
    # ------------------------------------------------------------------
    if args.srt:
        if not result.word_boundaries:
            log.warning(
                "No timing data received from TTS engine; "
                "SRT file will not be generated."
            )
        else:
            try:
                srt_path = generate_srt_file(
                    result.word_boundaries,
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
