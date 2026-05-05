"""AI-powered SSML generator for Edge-TTS (Vietnamese).

Supports two AI providers:
  - ``gemini``  — Google Gemini API (free tier, recommended)
  - ``openai``  — OpenAI ChatGPT API (requires billing)

Public API:
    generate_ssml(text, provider="gemini", api_key=None, model=None) -> str
    extract_ssml_body(ssml)                                          -> str
    save_ssml(ssml, path)                                            -> Path
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# System prompt — Vietnamese speech synthesis expert
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
Bạn là chuyên gia xử lý giọng nói (speech synthesis) cho tiếng Việt.

Chuyển đoạn văn bản thành SSML để dùng với Edge-TTS (giọng vi-VN-HoaiMyNeural), \
đảm bảo giọng đọc tự nhiên, có cảm xúc, giống người thật.

Yêu cầu:
* Chỉ trả về SSML hợp lệ (không giải thích, không markdown fence).
* Bọc toàn bộ trong thẻ <speak>.
* Sử dụng:
  * <break time="xxxms"/> để tạo ngắt nghỉ tự nhiên (200ms–600ms).
  * <emphasis level="moderate"> để nhấn mạnh từ/cụm quan trọng.
  * <prosody rate="" pitch=""> để điều chỉnh giọng theo cảm xúc.
* Chia đoạn hợp lý, không để câu quá dài.
* Không lạm dụng break hoặc emphasis.
* Giữ văn phong tự nhiên, không kịch quá.

Quy tắc cảm xúc:
* Câu bình thường:          rate="+10%" pitch="+4Hz"
* Câu hồi hộp / nhấn mạnh: rate="+5%"  pitch="+5Hz"
* Câu buồn / trầm:          rate="-5%"  pitch="+2Hz"
"""

# Default models
_DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
_DEFAULT_OPENAI_MODEL = "gpt-4o"


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------


def generate_ssml(
    text: str,
    *,
    provider: str = "gemini",
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """Convert plain Vietnamese *text* to SSML using an AI provider.

    Args:
        text:     Plain Vietnamese input text.
        provider: ``"gemini"`` (default, free tier) or ``"openai"`` (paid).
        api_key:  API key for the chosen provider. Falls back to env var:
                  ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY`` for Gemini,
                  ``OPENAI_API_KEY`` for OpenAI.
        model:    Model name override. Defaults to ``gemini-2.0-flash`` or
                  ``gpt-4o`` depending on provider.

    Returns:
        Full SSML string starting with ``<speak>``.
    """
    if provider == "gemini":
        return _generate_ssml_gemini(
            text, api_key=api_key, model=model or _DEFAULT_GEMINI_MODEL
        )
    if provider == "openai":
        return _generate_ssml_openai(
            text, api_key=api_key, model=model or _DEFAULT_OPENAI_MODEL
        )
    raise ValueError(
        f"Unknown AI provider '{provider}'. Choose: gemini, openai"
    )


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------


def _generate_ssml_gemini(
    text: str,
    *,
    api_key: str | None = None,
    model: str = _DEFAULT_GEMINI_MODEL,
) -> str:
    """Generate SSML using Google Gemini API (google-genai SDK)."""
    try:
        from google import genai  # noqa: PLC0415
        from google.genai import types as genai_types  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "google-genai package is required for Gemini SSML generation. "
            "Install with: pip install google-genai"
        ) from exc

    resolved_key = (
        api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not resolved_key:
        raise ValueError(
            "Gemini API key is required. "
            "Set GEMINI_API_KEY env var or pass --gemini-key. "
            "Get a free key at: https://aistudio.google.com/apikey"
        )

    client = genai.Client(api_key=resolved_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=text,
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    raw = response.text or ""
    return _clean_raw_response(raw)


# ---------------------------------------------------------------------------
# OpenAI backend
# ---------------------------------------------------------------------------


def _generate_ssml_openai(
    text: str,
    *,
    api_key: str | None = None,
    model: str = _DEFAULT_OPENAI_MODEL,
) -> str:
    """Generate SSML using OpenAI ChatGPT API."""
    try:
        from openai import OpenAI  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "openai package is required for OpenAI SSML generation. "
            "Install with: pip install openai"
        ) from exc

    resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not resolved_key:
        raise ValueError(
            "OpenAI API key is required. "
            "Set OPENAI_API_KEY env var or pass --openai-key."
        )

    client = OpenAI(api_key=resolved_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.4,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    raw = response.choices[0].message.content or ""
    return _clean_raw_response(raw)


# ---------------------------------------------------------------------------
# SSML helpers
# ---------------------------------------------------------------------------


def _clean_raw_response(raw: str) -> str:
    """Strip markdown code fences if the model wraps its output."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:xml)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def extract_ssml_body(ssml: str) -> str:
    """Extract inner SSML content suitable for passing to edge-tts.

    edge-tts wraps text in its own ``<speak><voice><prosody>`` envelope.
    To avoid double-wrapping, we strip the outer ``<speak>`` and ``<voice>``
    tags, keeping only the inner elements (``<prosody>``, ``<break>``,
    ``<emphasis>``, plain text, etc.).

    If parsing fails, falls back to a regex-based strip so TTS can still run.
    """
    try:
        ET.register_namespace("", "http://www.w3.org/2001/10/synthesis")
        ET.register_namespace("mstts", "https://www.w3.org/2001/mstts")

        root = ET.fromstring(ssml)
        body_parts: list[str] = []

        _xmlns_re = re.compile(r'\s+xmlns(?::\w+)?="[^"]*"')

        def _serialize_children(elem: ET.Element) -> str:
            parts = []
            if elem.text:
                parts.append(elem.text)
            for child in elem:
                serialized = ET.tostring(child, encoding="unicode")
                serialized = _xmlns_re.sub("", serialized)
                parts.append(serialized)
                if child.tail:
                    parts.append(child.tail)
            return "".join(parts)

        for child in root:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "voice":
                body_parts.append(_serialize_children(child))
            else:
                serialized = ET.tostring(child, encoding="unicode")
                serialized = _xmlns_re.sub("", serialized)
                body_parts.append(serialized)
                if child.tail:
                    body_parts.append(child.tail)

        if root.text:
            body_parts.insert(0, root.text)

        return "".join(body_parts).strip()

    except ET.ParseError:
        inner = re.sub(r"<\s*speak[^>]*>", "", ssml, flags=re.IGNORECASE)
        inner = re.sub(r"</\s*speak\s*>", "", inner, flags=re.IGNORECASE)
        inner = re.sub(r"<\s*voice[^>]*>", "", inner, flags=re.IGNORECASE)
        inner = re.sub(r"</\s*voice\s*>", "", inner, flags=re.IGNORECASE)
        return inner.strip()


def save_ssml(ssml: str, path: str | Path) -> Path:
    """Save SSML string to *path* and return the resolved Path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(ssml, encoding="utf-8")
    return out
