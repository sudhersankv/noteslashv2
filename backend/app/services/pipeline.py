"""Sync processing pipeline: categorize, chunk, embed, insights."""

from __future__ import annotations

from uuid import UUID

from app.db import get_supabase
from app.services.categorization import aggregate_project_metadata, categorize_transcript
from app.services.chunking import chunk_transcript
from app.services.embedding import embed_texts
from app.services.insights import extract_and_store_insights


def process_project(project_id: UUID) -> None:
    sb = get_supabase()
    pid = str(project_id)

    transcripts = (
        sb.table("transcripts")
        .select("*")
        .eq("project_id", pid)
        .in_("status", ["pending", "failed"])
        .execute()
    ).data or []

    if not transcripts:
        ready = (
            sb.table("transcripts")
            .select("id")
            .eq("project_id", pid)
            .eq("status", "ready")
            .execute()
        )
        if ready.data:
            return
        raise ValueError("No content to process")

    sb.table("chunks").delete().eq("project_id", pid).execute()
    sb.table("insights").delete().eq("project_id", pid).execute()

    for tr in transcripts:
        if not (tr.get("raw_text") or "").strip():
            sb.table("transcripts").update({"status": "failed"}).eq("id", tr["id"]).execute()
            continue

        sb.table("transcripts").update({"status": "processing"}).eq("id", tr["id"]).execute()
        try:
            categorize_transcript(tr["id"], tr["raw_text"], tr.get("filename"))

            chunks = chunk_transcript(tr["raw_text"])
            if not chunks:
                sb.table("transcripts").update({"status": "failed"}).eq("id", tr["id"]).execute()
                continue

            texts = [c.text for c in chunks]
            embeddings = embed_texts(texts)

            rows = []
            for c, emb in zip(chunks, embeddings):
                rows.append(
                    {
                        "transcript_id": tr["id"],
                        "project_id": pid,
                        "chunk_index": c.chunk_index,
                        "text": c.text,
                        "speaker": c.speaker,
                        "start_offset": c.start_offset,
                        "end_offset": c.end_offset,
                        "embedding": emb,
                    }
                )

            sb.table("chunks").insert(rows).execute()
            sb.table("transcripts").update({"status": "ready"}).eq("id", tr["id"]).execute()
        except Exception:
            sb.table("transcripts").update({"status": "failed"}).eq("id", tr["id"]).execute()
            raise

    aggregate_project_metadata(project_id)
    extract_and_store_insights(project_id)
