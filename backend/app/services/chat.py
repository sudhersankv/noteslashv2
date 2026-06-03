"""Multi-turn chat with RAG citations."""

from __future__ import annotations

import json
from uuid import UUID

from app.agents.prompts import CHAT_SYSTEM, CHAT_USER_TEMPLATE
from app.config import settings
from app.db import get_supabase
from app.models.schemas import ChatMessageItem, ChatResponse, Citation
from app.services.citations import rows_to_citations
from app.services.embedding import get_openai
from app.services.retrieval import retrieve_chunks

HISTORY_LIMIT = 12


def get_chat_history(project_id: UUID) -> list[ChatMessageItem]:
    sb = get_supabase()
    rows = (
        sb.table("chat_messages")
        .select("*")
        .eq("project_id", str(project_id))
        .order("created_at")
        .execute()
    ).data or []
    return [
        ChatMessageItem(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            citations=[
                Citation(**{**c, "transcript_id": c.get("transcript_id")})
                for c in (r.get("citations") or [])
                if c.get("chunk_id")
            ],
        )
        for r in rows
    ]


def chat_project(project_id: UUID, message: str) -> ChatResponse:
    sb = get_supabase()
    pid = str(project_id)

    sb.table("chat_messages").insert(
        {"project_id": pid, "role": "user", "content": message, "citations": []}
    ).execute()

    history = (
        sb.table("chat_messages")
        .select("role, content")
        .eq("project_id", pid)
        .order("created_at")
        .limit(HISTORY_LIMIT)
        .execute()
    ).data or []

    rows = retrieve_chunks(project_id, message, top_k=8)
    quotes_json = [
        {
            "chunk_id": r["id"],
            "filename": r.get("filename"),
            "text": r["text"],
        }
        for r in rows
    ]

    history_text = "\n".join(f"{h['role']}: {h['content']}" for h in history[-8:])

    client = get_openai()
    user_msg = CHAT_USER_TEMPLATE.format(
        history=history_text,
        message=message,
        quotes_json=json.dumps(quotes_json),
    )
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": CHAT_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    data = json.loads(response.choices[0].message.content or "{}")
    answer = data.get("answer", "")
    cited_ids = set(data.get("cited_chunk_ids", []))
    citations = rows_to_citations(rows, cited_ids if cited_ids else None)

    insert = (
        sb.table("chat_messages")
        .insert(
            {
                "project_id": pid,
                "role": "assistant",
                "content": answer,
                "citations": [c.model_dump(mode="json") for c in citations],
            }
        )
        .execute()
    )
    msg_id = insert.data[0]["id"] if insert.data else None
    return ChatResponse(answer=answer, citations=citations, message_id=msg_id)
