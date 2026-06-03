"""Shared citation building from retrieval rows."""

from __future__ import annotations

from app.models.schemas import Citation


def rows_to_citations(rows: list[dict], cited_ids: set | None = None) -> list[Citation]:
    citations: list[Citation] = []
    targets = rows if not cited_ids else [
        r for r in rows if str(r["id"]) in cited_ids or r["id"] in cited_ids
    ]

    if cited_ids and not targets:
        targets = rows[:3]
    elif not cited_ids:
        targets = rows[:5]

    for r in targets:
        citations.append(
            Citation(
                chunk_id=r["id"],
                transcript_id=r["transcript_id"],
                filename=r.get("filename"),
                text=r["text"],
                speaker=r.get("speaker"),
                similarity=r.get("similarity"),
            )
        )
    return citations


def snippets_from_rows(rows: list[dict], limit: int = 5) -> list[dict]:
    return [
        {
            "chunk_id": r["id"],
            "text": r["text"],
            "filename": r.get("filename", "source"),
            "similarity": r.get("similarity"),
        }
        for r in rows[:limit]
    ]
