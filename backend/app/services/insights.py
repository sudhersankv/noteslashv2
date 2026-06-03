"""Research agent: extract insights by content type."""

from __future__ import annotations

import json
from uuid import UUID

from app.agents.prompts import (
    RESEARCH_GENERAL_SYSTEM,
    RESEARCH_GENERAL_USER,
    RESEARCH_INTERVIEW_SYSTEM,
    RESEARCH_INTERVIEW_USER,
)
from app.config import settings
from app.db import get_supabase
from app.services.embedding import get_openai


def _filename_map(sb, transcript_ids: list[str]) -> dict[str, str]:
    if not transcript_ids:
        return {}
    tr = sb.table("transcripts").select("id, filename").in_("id", transcript_ids).execute()
    return {t["id"]: t.get("filename") or "source" for t in (tr.data or [])}


def _build_chunks_context(project_id: UUID, limit: int = 80) -> list[dict]:
    sb = get_supabase()
    chunks = (
        sb.table("chunks")
        .select("id, text, transcript_id")
        .eq("project_id", str(project_id))
        .limit(limit)
        .execute()
    )
    tids = list({c["transcript_id"] for c in (chunks.data or [])})
    fn_map = _filename_map(sb, tids)
    return [
        {
            "id": c["id"],
            "filename": fn_map.get(c["transcript_id"], "source"),
            "text": c["text"][:800],
        }
        for c in (chunks.data or [])
    ]


def _resolve_evidence(chunk_ids: list[str], chunk_map: dict[str, dict]) -> list[dict]:
    evidence = []
    for cid in chunk_ids:
        ch = chunk_map.get(cid) or chunk_map.get(str(cid))
        if not ch:
            continue
        evidence.append(
            {
                "chunk_id": cid,
                "transcript_id": ch.get("transcript_id"),
                "filename": ch.get("filename"),
                "quote": ch.get("text", "")[:500],
            }
        )
    return evidence


def _get_content_type(project_id: UUID) -> str:
    sb = get_supabase()
    project = sb.table("projects").select("content_type").eq("id", str(project_id)).execute()
    if project.data:
        return project.data[0].get("content_type") or "other"
    return "other"


def extract_and_store_insights(project_id: UUID) -> str:
    sb = get_supabase()
    pid = str(project_id)
    sb.table("insights").delete().eq("project_id", pid).execute()

    chunks_ctx = _build_chunks_context(project_id)
    if not chunks_ctx:
        return "No content available."

    all_chunks = sb.table("chunks").select("id, text, transcript_id").eq("project_id", pid).execute()
    tids = list({c["transcript_id"] for c in (all_chunks.data or [])})
    fn_map = _filename_map(sb, tids)
    chunk_map = {
        c["id"]: {
            "text": c["text"],
            "transcript_id": c["transcript_id"],
            "filename": fn_map.get(c["transcript_id"], "source"),
        }
        for c in (all_chunks.data or [])
    }

    content_type = _get_content_type(project_id)
    if content_type == "interview":
        system, user_tpl = RESEARCH_INTERVIEW_SYSTEM, RESEARCH_INTERVIEW_USER
    else:
        system, user_tpl = RESEARCH_GENERAL_SYSTEM, RESEARCH_GENERAL_USER

    client = get_openai()
    user_msg = user_tpl.format(chunks_json=json.dumps(chunks_ctx[:60]))
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    data = json.loads(response.choices[0].message.content or "{}")
    summary = data.get("summary", "")

    type_map = {
        "themes": "theme",
        "pain_points": "pain_point",
        "feature_requests": "feature_request",
    }

    for key, insight_type in type_map.items():
        for item in data.get(key, []):
            chunk_ids = item.get("chunk_ids", [])
            evidence = _resolve_evidence(chunk_ids, chunk_map)

            sb.table("insights").insert(
                {
                    "project_id": pid,
                    "type": insight_type,
                    "title": item.get("title", "Untitled"),
                    "description": item.get("description"),
                    "frequency": item.get("frequency"),
                    "confidence": item.get("confidence"),
                    "evidence": evidence,
                }
            ).execute()

    return summary
