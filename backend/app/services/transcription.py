"""OpenAI Whisper transcription."""

from __future__ import annotations

import io

from app.config import settings
from app.services.embedding import get_openai


def transcribe_audio(content: bytes, filename: str) -> str:
    client = get_openai()
    buffer = io.BytesIO(content)
    buffer.name = filename or "audio.mp3"
    response = client.audio.transcriptions.create(
        model=settings.openai_whisper_model,
        file=buffer,
        response_format="text",
    )
    if isinstance(response, str):
        return response.strip()
    return str(response).strip()
