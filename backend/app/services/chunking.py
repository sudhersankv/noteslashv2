"""Transcript chunking: speaker turns with token-window fallback."""

from __future__ import annotations

import re
from dataclasses import dataclass

import tiktoken

from app.config import settings

SPEAKER_PATTERN = re.compile(
    r"^(?:(?:Interviewer|Participant|User|Customer|Host|Guest|Speaker)\s*[:\-–—]|\w[\w\s]{0,30}:\s)",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class TextChunk:
    text: str
    speaker: str | None
    start_offset: int
    end_offset: int
    chunk_index: int


def _get_encoding():
    try:
        return tiktoken.encoding_for_model("gpt-4")
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def _split_by_speaker(text: str) -> list[tuple[str | None, str, int, int]]:
    """Return list of (speaker, content, start, end)."""
    matches = list(SPEAKER_PATTERN.finditer(text))
    if not matches:
        return [(None, text.strip(), 0, len(text))]

    segments: list[tuple[str | None, str, int, int]] = []
    for i, match in enumerate(matches):
        start = int(match.start())
        end = int(matches[i + 1].start()) if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        if not block:
            continue
        line_end = block.find("\n")
        header = block if line_end == -1 else block[:line_end]
        speaker_match = re.match(r"^([^:：\-–—]+)", header)
        speaker = speaker_match.group(1).strip() if speaker_match else None
        segments.append((speaker, block, start, end))
    return segments


def _token_split(text: str, max_tokens: int, overlap: int) -> list[str]:
    enc = _get_encoding()
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return [text]

    parts: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        parts.append(enc.decode(tokens[start:end]))
        if end >= len(tokens):
            break
        start = end - overlap
    return parts


def chunk_transcript(text: str) -> list[TextChunk]:
    """Chunk transcript by speaker turns; split large turns by tokens."""
    max_tokens = settings.chunk_size_tokens
    overlap = settings.chunk_overlap_tokens
    segments = _split_by_speaker(text)
    chunks: list[TextChunk] = []
    idx = 0

    for speaker, segment_text, seg_start, _seg_end in segments:
        if not segment_text.strip():
            continue
        token_parts = _token_split(segment_text, max_tokens, overlap)
        for part in token_parts:
            part = part.strip()
            if len(part) < 20:
                continue
            chunks.append(
                TextChunk(
                    text=part,
                    speaker=speaker,
                    start_offset=seg_start,
                    end_offset=seg_start + len(part),
                    chunk_index=idx,
                )
            )
            idx += 1

    if not chunks and text.strip():
        for part in _token_split(text.strip(), max_tokens, overlap):
            if len(part.strip()) >= 20:
                chunks.append(
                    TextChunk(
                        text=part.strip(),
                        speaker=None,
                        start_offset=0,
                        end_offset=len(part),
                        chunk_index=idx,
                    )
                )
                idx += 1

    return chunks
