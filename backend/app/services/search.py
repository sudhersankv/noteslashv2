"""RAG search with cited answers."""

from __future__ import annotations

import json
from uuid import UUID

from app.agents.prompts import SEARCH_SYSTEM, SEARCH_USER_TEMPLATE
from app.config import settings
from app.models.schemas import SearchResponse
from app.services.citations import rows_to_citations
from app.services.embedding import get_openai
from app.services.retrieval import retrieve_chunks


def search_project(project_id: UUID, query: str) -> SearchResponse:
    rows = retrieve_chunks(project_id, query)
    if not rows:
        return SearchResponse(
            answer="No relevant quotes found in the transcripts for this question.",
            citations=[],
        )

    quotes_json = [
        {
            "chunk_id": r["id"],
            "filename": r.get("filename"),
            "speaker": r.get("speaker"),
            "text": r["text"],
            "similarity": r.get("similarity"),
        }
        for r in rows
    ]

    client = get_openai()
    user_msg = SEARCH_USER_TEMPLATE.format(
        query=query,
        quotes_json=json.dumps(quotes_json),
    )
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": SEARCH_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)
    answer = data.get("answer", "")
    cited_ids = set(data.get("cited_chunk_ids", []))
    citations = rows_to_citations(rows, cited_ids if cited_ids else None)

    return SearchResponse(answer=answer, citations=citations)
