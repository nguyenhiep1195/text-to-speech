"""TTS routes – supports both job-based (local) and sync-zip (Vercel) flows."""
from __future__ import annotations

import io
import sys
import uuid
import logging
import threading
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response

from ..auth import get_current_user
from ..models import TTSRequest, JobResponse, JobStatus

# ---------------------------------------------------------------------------
# Import TTS engine – prefer backend/src/ (Vercel), fall back to repo root src/
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).parent.parent.parent   # backend/
_REPO_ROOT = _BACKEND_DIR.parent                     # text-to-speech/

for _p in [str(_BACKEND_DIR), str(_REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.tts import convert_text, VOICE_PRESETS  # noqa: E402
from src.srt import generate_srt_file           # noqa: E402

router = APIRouter(tags=["tts"])
logger = logging.getLogger(__name__)

# In-memory job store (local dev only – not shared across serverless invocations)
_jobs: dict[str, dict] = {}
_TEMP_DIR = Path(tempfile.gettempdir()) / "tts_jobs"
_TEMP_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_voice_params(voice: str) -> dict:
    if voice in VOICE_PRESETS:
        preset = VOICE_PRESETS[voice]
        return {"voice": preset.voice, "rate": preset.rate, "pitch": preset.pitch, "volume": "+0%"}
    return {"voice": voice, "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}


def _detect_lang(voice: str) -> str:
    return "vi" if voice.startswith("vi") else "en"


def _run_tts_to_dir(req: TTSRequest, job_dir: Path) -> tuple[Path, Optional[Path]]:
    """Run TTS synchronously; return (mp3_path, srt_path_or_None)."""
    mp3_path = job_dir / "output.mp3"
    srt_path = job_dir / "output.srt"
    job_dir.mkdir(parents=True, exist_ok=True)

    vp = _resolve_voice_params(req.voice)
    result = convert_text(
        req.text,
        mp3_path,
        engine_name=req.engine.value,
        voice=vp["voice"],
        rate=vp["rate"],
        pitch=vp["pitch"],
        volume=vp["volume"],
        lang=_detect_lang(req.voice),
        speed=req.speed,
    )

    srt_out: Optional[Path] = None
    if req.engine.value == "edge-tts" and result.boundaries:
        try:
            generate_srt_file(result.boundaries, srt_path, words_per_cue=req.words_per_cue)
            srt_out = srt_path
        except Exception as exc:
            logger.warning("SRT generation failed: %s", exc)

    return mp3_path, srt_out


def _run_tts_job(job_id: str, req: TTSRequest) -> None:
    job = _jobs[job_id]
    job["status"] = JobStatus.processing
    job_dir = _TEMP_DIR / job_id
    try:
        mp3_path, srt_path = _run_tts_to_dir(req, job_dir)
        job.update({
            "status": JobStatus.done,
            "has_mp3": mp3_path.exists(),
            "has_srt": srt_path is not None and srt_path.exists(),
            "mp3_path": str(mp3_path),
            "srt_path": str(srt_path) if srt_path else None,
        })
    except Exception as exc:
        logger.exception("Job %s failed: %s", job_id, exc)
        job.update({"status": JobStatus.error, "message": str(exc)})


# ---------------------------------------------------------------------------
# Routes – Voices
# ---------------------------------------------------------------------------

@router.get("/voices")
async def get_voices(_: dict = Depends(get_current_user)):
    voices = []
    for preset_id, preset in VOICE_PRESETS.items():
        gender = (
            "female"
            if "female" in preset_id or "HoaiMy" in preset.voice or "Aria" in preset.voice
            else "male"
        )
        voices.append({
            "id": preset_id,
            "name": preset.desc,
            "voice": preset.voice,
            "gender": gender,
            "lang": "vi" if preset_id.startswith("vi") else "en",
            "rate": preset.rate,
            "pitch": preset.pitch,
        })
    return {"voices": voices}


# ---------------------------------------------------------------------------
# Routes – Synchronous convert → ZIP (Vercel-compatible)
# ---------------------------------------------------------------------------

@router.post("/tts/convert")
async def convert_sync(req: TTSRequest, _: dict = Depends(get_current_user)):
    """
    Synchronous TTS conversion. Returns a ZIP archive containing:
    - output.mp3  (always present)
    - output.srt  (only when engine=edge-tts and timing data is available)

    Use this endpoint for serverless/Vercel deployments.
    """
    job_dir = _TEMP_DIR / str(uuid.uuid4())
    try:
        mp3_path, srt_path = _run_tts_to_dir(req, job_dir)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            if mp3_path.exists():
                zf.write(mp3_path, "output.mp3")
            if srt_path and srt_path.exists():
                zf.write(srt_path, "output.srt")

        buf.seek(0)
        return Response(
            content=buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="tts-output.zip"'},
        )
    except Exception as exc:
        logger.exception("Sync TTS failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        # Clean up temp files
        import shutil
        shutil.rmtree(job_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Routes – Job-based (local dev only)
# ---------------------------------------------------------------------------

@router.post("/tts", response_model=JobResponse)
async def create_tts_job(
    req: TTSRequest,
    background_tasks: BackgroundTasks,
    _: dict = Depends(get_current_user),
):
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": JobStatus.pending,
        "has_mp3": False,
        "has_srt": False,
        "mp3_path": None,
        "srt_path": None,
        "message": None,
    }
    thread = threading.Thread(target=_run_tts_job, args=(job_id, req), daemon=True)
    thread.start()
    return JobResponse(job_id=job_id, status=JobStatus.pending)


@router.get("/tts/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, _: dict = Depends(get_current_user)):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        job_id=job_id,
        status=job["status"],
        message=job.get("message"),
        has_mp3=job.get("has_mp3", False),
        has_srt=job.get("has_srt", False),
    )


@router.get("/tts/{job_id}/download/mp3")
async def download_mp3(job_id: str, _: dict = Depends(get_current_user)):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != JobStatus.done or not job.get("mp3_path"):
        raise HTTPException(status_code=400, detail="MP3 not ready")
    mp3_path = Path(job["mp3_path"])
    if not mp3_path.exists():
        raise HTTPException(status_code=404, detail="MP3 file missing")
    return FileResponse(path=str(mp3_path), media_type="audio/mpeg", filename="output.mp3")


@router.get("/tts/{job_id}/download/srt")
async def download_srt(job_id: str, _: dict = Depends(get_current_user)):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != JobStatus.done or not job.get("srt_path"):
        raise HTTPException(status_code=400, detail="SRT not ready")
    srt_path = Path(job["srt_path"])
    if not srt_path.exists():
        raise HTTPException(status_code=404, detail="SRT file missing")
    return FileResponse(
        path=str(srt_path),
        media_type="text/plain; charset=utf-8",
        filename="output.srt",
    )
