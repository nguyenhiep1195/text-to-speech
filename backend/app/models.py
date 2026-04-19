from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class EngineEnum(str, Enum):
    edge_tts = "edge-tts"
    gtts = "gtts"


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to convert (up to 500k words)")
    voice: str = Field(default="vi-female", description="Voice preset or raw voice name")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speed multiplier")
    engine: EngineEnum = Field(default=EngineEnum.edge_tts)
    words_per_cue: int = Field(default=8, ge=1, le=20)


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: Optional[str] = None
    has_mp3: bool = False
    has_srt: bool = False
