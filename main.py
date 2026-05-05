#!/usr/bin/env python3
"""Entry point for the Text-to-Speech CLI.

Reads text from ``input/*.txt``. Default audio layout::
    output/<tên-file-gốc>/audio.mp3

Usage:
    python main.py --input sample.txt --voice vi-female-story --srt
    python main.py --input sample.txt --voice vi-female-story --srt-only
    python main.py   # convert all *.txt in input/
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Load .env file if present (provides OPENAI_API_KEY etc.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    from src.cli import (
        apply_output_paths_for_input,
        build_parser,
        collect_input_txt_paths,
        resolve_args,
    )
    from src.paths import INPUT_DIR
    from src.tts import list_vietnamese_voices, list_presets
    from src.engines import ENGINES

    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "srt_only", False):
        args.srt = True
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
    # Resolve input file(s)
    # ------------------------------------------------------------------
    input_paths = collect_input_txt_paths(args.input)
    if not input_paths:
        parser.error(
            f"No .txt files found in {INPUT_DIR}. "
            "Add files or pass --input FILE."
        )

    multi = len(input_paths) > 1
    if multi and args.output is not None:
        parser.error("--output/-o cannot be used when converting multiple inputs.")
    if multi and args.srt_output is not None:
        parser.error("--srt-output cannot be used when converting multiple inputs.")
    if multi and args.save_ssml is not None:
        parser.error("--save-ssml cannot be used when converting multiple inputs.")

    if getattr(args, "srt_only", False) and args.engine != "edge-tts":
        parser.error("--srt-only requires --engine edge-tts.")

    try:
        args = resolve_args(args)
    except ValueError as exc:
        parser.error(str(exc))

    overall_rc = 0

    for input_path in input_paths:
        apply_output_paths_for_input(args, input_path)

        rc = _convert_one(args, input_path, log)
        if rc != 0:
            overall_rc = rc

    print()
    return overall_rc


def _convert_one(
    args: argparse.Namespace,
    input_path: Path,
    log: logging.Logger,
) -> int:
    from src.tts import convert_text
    from src.srt import generate_srt_file
    from src.utils import read_text_file
    from src.ssml import generate_ssml, extract_ssml_body, save_ssml

    output_path = Path(args.output)
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
    if getattr(args, "srt_only", False):
        log.info("Mode   : SRT-only (no MP3 will be written)")

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
    # AI SSML generation (optional)
    # ------------------------------------------------------------------
    ssml_mode = False
    tts_text = text

    if getattr(args, "ai_ssml", False):
        if args.engine != "edge-tts":
            log.warning("--ai-ssml is only supported with --engine edge-tts. Ignoring.")
        else:
            provider = getattr(args, "ai_provider", "gemini")
            if provider == "gemini":
                ai_key   = getattr(args, "gemini_key", None)
                ai_model = getattr(args, "gemini_model", "gemini-2.0-flash")
            else:
                ai_key   = getattr(args, "openai_key", None)
                ai_model = getattr(args, "openai_model", "gpt-4o")

            log.info("Generating SSML via %s (%s)…", provider.upper(), ai_model)
            try:
                full_ssml = generate_ssml(
                    text,
                    provider=provider,
                    api_key=ai_key,
                    model=ai_model,
                )
            except (ImportError, ValueError, RuntimeError) as exc:
                log.error("SSML generation failed: %s", exc)
                return 6

            # Save SSML next to audio unless --save-ssml overrides
            ssml_path = save_ssml(full_ssml, args.save_ssml)
            print(f"✓  SSML saved   →  {ssml_path}")
            if args.verbose:
                log.debug("Generated SSML:\n%s", full_ssml)

            # Strip outer <speak>/<voice> so edge-tts can wrap properly
            tts_text = extract_ssml_body(full_ssml)
            ssml_mode = True
            log.info("SSML body extracted (%d chars)", len(tts_text))

    # ------------------------------------------------------------------
    # TTS conversion
    # ------------------------------------------------------------------
    try:
        result = convert_text(
            tts_text,
            output_path,
            engine_name=args.engine,
            # edge-tts params
            voice=getattr(args, "voice", "vi-VN-HoaiMyNeural"),
            rate=getattr(args, "rate", "+0%"),
            pitch=getattr(args, "pitch", "+0Hz"),
            volume=getattr(args, "volume", "+0%"),
            ssml_mode=ssml_mode,
            # common params
            lang=args.lang,
            speed=args.speed or 1.0,
            write_audio=not getattr(args, "srt_only", False),
        )
    except ImportError as exc:
        log.error("%s", exc)
        return 4
    except Exception as exc:
        log.error("TTS conversion failed: %s", exc)
        if args.verbose:
            log.exception("Traceback:")
        return 4

    if not getattr(args, "srt_only", False):
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
