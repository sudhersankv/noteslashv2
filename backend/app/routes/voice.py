"""Voice Realtime API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db import get_supabase
from app.models.schemas import VoiceSessionResponse, VoiceToolRequest, VoiceToolResponse
from app.services.citations import snippets_from_rows
from app.services.realtime import create_realtime_session
from app.services.retrieval import retrieve_chunks

router = APIRouter(prefix="/api/projects", tags=["voice"])


def _get_project_or_404(project_id: UUID) -> dict:
    sb = get_supabase()
    result = sb.table("projects").select("*").eq("id", str(project_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Library not found")
    return result.data[0]


@router.post("/{project_id}/voice/session", response_model=VoiceSessionResponse)
def voice_session(project_id: UUID):
    project = _get_project_or_404(project_id)
    chunks = (
        get_supabase()
        .table("chunks")
        .select("id", count="exact")
        .eq("project_id", str(project_id))
        .execute()
    )
    if not (chunks.count or 0):
        raise HTTPException(status_code=400, detail="Process your library before using voice")

    try:
        session = create_realtime_session(project_id, project["name"])
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not create voice session: {e}",
        ) from e

    client_secret = session.get("client_secret", {})
    return VoiceSessionResponse(
        client_secret=client_secret.get("value", ""),
        expires_at=client_secret.get("expires_at"),
        model=session.get("model", ""),
    )


@router.post("/{project_id}/voice/tool", response_model=VoiceToolResponse)
def voice_tool(project_id: UUID, body: VoiceToolRequest):
    _get_project_or_404(project_id)
    rows = retrieve_chunks(project_id, body.query, top_k=5)
    return VoiceToolResponse(snippets=snippets_from_rows(rows))
