"""TTS conversion and voice listing endpoints."""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tts"])


# ── Request / Response models ────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    voice: str = "vi-female"
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: str = "+0Hz"
    engine: str = "edge-tts"
    generate_srt: bool = False
    words_per_cue: int = Field(8, ge=1, le=30)


class SRTRequest(BaseModel):
    text: str
    voice: str = "vi-female"
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: str = "+0Hz"
    engine: str = "edge-tts"
    words_per_cue: int = Field(8, ge=1, le=30)


class VoiceInfo(BaseModel):
    key: str
    voice: str
    rate: str
    pitch: str
    desc: str
    lang: str


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


# ── GET /api/voices ──────────────────────────────────────────────────────

@router.get("/voices")
async def list_voices():
    from src.tts import VOICE_PRESETS
    from src.engines import ENGINES

    voices = []
    for key, preset in VOICE_PRESETS.items():
        lang = "vi" if key.startswith("vi-") else "en"
        voices.append(VoiceInfo(
            key=key,
            voice=preset.voice,
            rate=preset.rate,
            pitch=preset.pitch,
            desc=preset.desc,
            lang=lang,
        ))

    return {
        "voices": [v.model_dump() for v in voices],
        "engines": list(ENGINES.keys()),
    }


# ── POST /api/tts/convert ───────────────────────────────────────────────

@router.post("/tts/convert")
async def convert_tts(req: TTSRequest, request: Request):
    from src.tts import VOICE_PRESETS
    from src.srt import build_srt
    from src.engines import get_engine

    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    preset = VOICE_PRESETS.get(req.voice)
    voice_name = preset.voice if preset else req.voice
    rate = _speed_to_rate(req.speed)
    pitch = req.pitch
    lang = "vi" if req.voice.startswith("vi") else "en"

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        async def on_progress(current: int, total: int):
            await queue.put(("progress", {"chunk": current, "total": total}))

        async def run_tts():
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    audio_path = Path(tmpdir) / "output.mp3"
                    engine = get_engine(req.engine)

                    if req.engine == "edge-tts":
                        result = await engine._convert_async(
                            text, audio_path, voice_name, rate, pitch, "+0%",
                            write_audio=True, on_progress=on_progress,
                        )
                    else:
                        result = await asyncio.to_thread(
                            engine.convert, text, audio_path,
                            lang=lang, speed=req.speed,
                        )

                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        if result.audio_path.exists():
                            zf.write(result.audio_path, "output.mp3")
                        if req.generate_srt and result.boundaries:
                            srt_doc = build_srt(result.boundaries, words_per_cue=req.words_per_cue)
                            zf.writestr("output.srt", srt_doc.to_string())

                    buf.seek(0)
                    zip_b64 = base64.b64encode(buf.read()).decode("ascii")
                    await queue.put(("done", zip_b64))
            except asyncio.CancelledError:
                await queue.put(("cancelled", None))
            except Exception as exc:
                logger.exception("TTS conversion failed")
                await queue.put(("error", str(exc)))

        task = asyncio.create_task(run_tts())

        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    return

                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                event_type, payload = msg
                if event_type == "progress":
                    yield _sse("progress", json.dumps(payload))
                elif event_type == "done":
                    yield _sse("done", payload)
                    return
                elif event_type == "error":
                    yield _sse("error", json.dumps({"detail": payload}))
                    return
                elif event_type == "cancelled":
                    return
        except asyncio.CancelledError:
            task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── POST /api/tts/srt ─────────────────────────────────────────────────

@router.post("/tts/srt")
async def generate_srt(req: SRTRequest, request: Request):
    from src.tts import VOICE_PRESETS
    from src.srt import build_srt
    from src.engines import get_engine

    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    preset = VOICE_PRESETS.get(req.voice)
    voice_name = preset.voice if preset else req.voice
    rate = _speed_to_rate(req.speed)
    pitch = req.pitch
    lang = "vi" if req.voice.startswith("vi") else "en"

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        async def on_progress(current: int, total: int):
            await queue.put(("progress", {"chunk": current, "total": total}))

        async def run_tts():
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    audio_path = Path(tmpdir) / "output.mp3"
                    engine = get_engine(req.engine)

                    if req.engine == "edge-tts":
                        result = await engine._convert_async(
                            text, audio_path, voice_name, rate, pitch, "+0%",
                            write_audio=False, on_progress=on_progress,
                        )
                    else:
                        result = await asyncio.to_thread(
                            engine.convert, text, audio_path,
                            lang=lang, speed=req.speed,
                        )

                    if not result.boundaries:
                        await queue.put(("error", "No word boundaries returned by engine."))
                        return

                    srt_doc = build_srt(result.boundaries, words_per_cue=req.words_per_cue)
                    await queue.put(("done", srt_doc.to_string()))
            except asyncio.CancelledError:
                await queue.put(("cancelled", None))
            except Exception as exc:
                logger.exception("TTS SRT generation failed")
                await queue.put(("error", str(exc)))

        task = asyncio.create_task(run_tts())

        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    return

                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                event_type, payload = msg
                if event_type == "progress":
                    yield _sse("progress", json.dumps(payload))
                elif event_type == "done":
                    yield _sse("done", payload)
                    return
                elif event_type == "error":
                    yield _sse("error", json.dumps({"detail": payload}))
                    return
                elif event_type == "cancelled":
                    return
        except asyncio.CancelledError:
            task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _speed_to_rate(speed: float) -> str:
    pct = round((speed - 1.0) * 100)
    return f"{pct:+d}%"
