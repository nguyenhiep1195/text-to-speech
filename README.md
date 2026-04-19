# Text-to-Speech (TTS) CLI Tool

A production-ready Python CLI that converts `.txt` files to `.mp3` audio using Microsoft Edge neural voices, with optional `.srt` subtitle generation. Vietnamese language is fully supported with natural-sounding neural voices.

---

## Features

- **Vietnamese-first** — uses `vi-VN-HoaiMyNeural` (female) or `vi-VN-NamMinhNeural` (male) by default
- **Multiple languages** — any edge-tts voice is supported
- **Auto-chunking** — long texts are split at sentence boundaries to stay within API limits
- **SRT subtitles** — word-level timestamps directly from the TTS engine
- **Clean architecture** — separate `tts`, `srt`, `utils`, `cli` modules
- **Robust encoding handling** — UTF-8, UTF-8-BOM, UTF-16, Latin-1, CP1252

---

## Project Structure

```
text-to-speech/
├── main.py             # CLI entry point
├── requirements.txt
├── public/             # Drop your .txt input files here
│   └── sample.txt
├── output/             # Generated audio/subtitle files (auto-created)
└── src/
    ├── __init__.py
    ├── cli.py          # Argument parsing
    ├── tts.py          # TTS engine (edge-tts)
    ├── srt.py          # SRT subtitle builder
    └── utils.py        # File I/O, chunking, helpers
```

---

## Requirements

- Python 3.10+
- Internet connection (edge-tts calls Microsoft's online TTS service)

---

## Installation

```bash
# Clone / enter the project
cd text-to-speech

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Basic conversion

```bash
python main.py --input public/sample.txt
# → output/sample.mp3
```

### Custom output path

```bash
python main.py --input public/sample.txt --output output/audio.mp3
```

### With SRT subtitles

```bash
python main.py --input public/sample.txt --output output/audio.mp3 --srt
# → output/audio.mp3
# → output/audio.srt
```

### Male voice, faster rate

```bash
python main.py --input public/sample.txt --voice vi-VN-NamMinhNeural --rate +15%
```

### Use voice shortcut

```bash
python main.py --input public/sample.txt --voice vi-male
```

| Shortcut    | Full voice name              |
|-------------|------------------------------|
| `vi-female` | `vi-VN-HoaiMyNeural`         |
| `vi-male`   | `vi-VN-NamMinhNeural`        |
| `en-female` | `en-US-AriaNeural`           |
| `en-male`   | `en-US-GuyNeural`            |

### List all Vietnamese voices

```bash
python main.py --list-voices
```

### Full options

```
Options:
  --input  / -i   FILE   Input .txt file path (required)
  --output / -o   FILE   Output .mp3 file path (default: output/<stem>.mp3)
  --srt                  Generate .srt subtitle file
  --srt-output    FILE   Custom SRT output path
  --words-per-cue N      Words per subtitle cue (default: 8)
  --voice         VOICE  Voice name or shortcut (default: vi-VN-HoaiMyNeural)
  --rate          RATE   Speech rate offset, e.g. +10% or -5% (default: +0%)
  --volume        VOL    Volume offset, e.g. +10% (default: +0%)
  --list-voices          List Vietnamese voices and exit
  --verbose / -v         Enable debug logging
```

---

## SRT Format

Generated `.srt` files follow the standard SubRip format:

```
1
00:00:00,000 --> 00:00:03,240
Xin chào, đây là bài kiểm tra

2
00:00:03,290 --> 00:00:06,850
chuyển đổi văn bản thành giọng nói.
```

Timestamps are sourced directly from the TTS engine's word-boundary events, so they are accurate to the millisecond.

---

## Error Handling

| Situation | Exit code |
|---|---|
| Input file not found | `2` |
| Empty file / encoding error | `3` |
| TTS conversion failure | `4` |
| SRT generation failure | `5` |

---

## Notes

- edge-tts requires an **internet connection** — it calls the Microsoft Edge TTS service.
- There is no official rate limit documented, but avoid hammering the service in a tight loop.
- For offline TTS, consider `pyttsx3` (lower voice quality) or a locally hosted Coqui TTS model.
