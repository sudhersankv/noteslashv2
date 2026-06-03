"""Media type detection for uploads."""

from __future__ import annotations

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".webm",
    ".ogg",
    ".mpeg",
    ".mpga",
    ".flac",
    ".aac",
}

AUDIO_MIME_PREFIXES = ("audio/",)


def is_audio_file(filename: str, content_type: str | None) -> bool:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in AUDIO_EXTENSIONS:
        return True
    if content_type and any(content_type.startswith(p) for p in AUDIO_MIME_PREFIXES):
        return True
    return False
