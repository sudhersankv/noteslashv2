"""Content categorization after transcription."""

from __future__ import annotations

import json
from collections import Counter
from uuid import UUID

from app.agents.prompts import CATEGORIZE_SYSTEM, CATEGORIZE_USER_TEMPLATE
from app.config import settings
from app.db import get_supabase
from app.services.embedding import get_openai

VALID_TYPES = {"podcast", "interview", "audiobook", "lecture", "other"}


def categorize_text(text: str, filename: str | None = None) -> dict:
    sample = text[:3000]
    client = get_openai()
    user_msg = CATEGORIZE_USER_TEMPLATE.format(
        filename=filename or "unknown",
        text=sample,
    )
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": CATEGORIZE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    data = json.loads(response.choices[0].message.content or "{}")
    content_type = data.get("content_type", "other")
    if content_type not in VALID_TYPES:
        content_type = "other"
    return {
        "content_type": content_type,
        "title_guess": data.get("title_guess"),
        "tags": data.get("tags", [])[:10],
        "summary": data.get("summary", ""),
    }


def categorize_transcript(transcript_id: str, text: str, filename: str | None) -> dict:
    result = categorize_text(text, filename)
    sb = get_supabase()
    sb.table("transcripts").update(
        {
            "content_type": result["content_type"],
            "title_guess": result.get("title_guess"),
            "tags": result.get("tags", []),
        }
    ).eq("id", transcript_id).execute()
    return result


def aggregate_project_metadata(project_id: UUID) -> None:
    sb = get_supabase()
    pid = str(project_id)
    rows = (
        sb.table("transcripts")
        .select("content_type, tags")
        .eq("project_id", pid)
        .execute()
    ).data or []

    types = [r["content_type"] for r in rows if r.get("content_type")]
    dominant = Counter(types).most_common(1)[0][0] if types else "other"

    all_tags: list[str] = []
    for r in rows:
        all_tags.extend(r.get("tags") or [])
    tag_counts = Counter(all_tags)
    top_tags = [t for t, _ in tag_counts.most_common(8)]

    sb.table("projects").update(
        {"content_type": dominant, "tags": top_tags}
    ).eq("id", pid).execute()
