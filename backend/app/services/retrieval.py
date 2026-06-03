"""Vector retrieval via Supabase match_chunks RPC."""

from __future__ import annotations

from uuid import UUID

from app.config import settings
from app.db import get_supabase
from app.services.embedding import embed_texts


def retrieve_chunks(project_id: UUID, query: str, top_k: int | None = None) -> list[dict]:
    k = top_k or settings.retrieval_top_k
    query_embedding = embed_texts([query])[0]

    sb = get_supabase()
    result = sb.rpc(
        "match_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": k,
            "filter_project_id": str(project_id),
        },
    ).execute()

    rows = result.data or []
    transcript_ids = {r["transcript_id"] for r in rows if r.get("transcript_id")}
    filenames: dict[str, str] = {}
    if transcript_ids:
        tr = (
            sb.table("transcripts")
            .select("id, filename")
            .in_("id", list(transcript_ids))
            .execute()
        )
        for t in tr.data or []:
            filenames[t["id"]] = t.get("filename") or "transcript"

    for row in rows:
        tid = row.get("transcript_id")
        row["filename"] = filenames.get(tid, "transcript")

    return rows
