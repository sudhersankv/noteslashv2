"""Grounding evaluation for insights."""

from __future__ import annotations

import json
from uuid import UUID

from app.agents.prompts import EVAL_JUDGE_SYSTEM, EVAL_JUDGE_USER_TEMPLATE
from app.config import settings
from app.db import get_supabase
from app.models.schemas import EvalMetrics, EvalResponse, UnsupportedItem
from app.services.embedding import get_openai


def run_evaluation(project_id: UUID) -> EvalResponse:
    sb = get_supabase()
    insights = (
        sb.table("insights")
        .select("*")
        .eq("project_id", str(project_id))
        .execute()
    ).data or []

    client = get_openai()
    unsupported_items: list[UnsupportedItem] = []
    grounded_insight_ids: set[str] = set()

    for ins in insights:
        evidence = ins.get("evidence") or []
        if not evidence:
            unsupported_items.append(
                UnsupportedItem(
                    insight_id=ins["id"],
                    insight_title=ins["title"],
                    reason="No evidence quotes attached",
                )
            )
            continue

        insight_supported = True
        for ev in evidence[:1]:
            quote = ev.get("quote", "")
            chunk_id = ev.get("chunk_id")

            if chunk_id:
                ch = sb.table("chunks").select("id, text").eq("id", chunk_id).execute()
                if not ch.data:
                    insight_supported = False
                    unsupported_items.append(
                        UnsupportedItem(
                            insight_id=ins["id"],
                            insight_title=ins["title"],
                            reason=f"Chunk {chunk_id} not found in database",
                        )
                    )
                    break
                quote = ch.data[0]["text"]

            if not quote.strip():
                insight_supported = False
                unsupported_items.append(
                    UnsupportedItem(
                        insight_id=ins["id"],
                        insight_title=ins["title"],
                        reason="Empty quote text",
                    )
                )
                break

            user_msg = EVAL_JUDGE_USER_TEMPLATE.format(
                title=ins["title"],
                description=ins.get("description") or "",
                quote=quote[:600],
            )
            response = client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[
                    {"role": "system", "content": EVAL_JUDGE_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            result = json.loads(response.choices[0].message.content or "{}")
            if not result.get("supported"):
                insight_supported = False
                unsupported_items.append(
                    UnsupportedItem(
                        insight_id=ins["id"],
                        insight_title=ins["title"],
                        reason=result.get("reason", "Quote does not support insight"),
                    )
                )

        if insight_supported:
            grounded_insight_ids.add(str(ins["id"]))

    insights_total = len(insights)
    grounded_insights = len(grounded_insight_ids)
    unsupported_count = insights_total - grounded_insights
    score = (grounded_insights / insights_total * 100) if insights_total else 100.0

    metrics = EvalMetrics(
        insights_total=insights_total,
        grounded=grounded_insights,
        unsupported=unsupported_count,
        grounding_score=round(score, 1),
    )

    insert = (
        sb.table("eval_runs")
        .insert(
            {
                "project_id": str(project_id),
                "metrics": metrics.model_dump(),
                "unsupported_items": [u.model_dump(mode="json") for u in unsupported_items],
            }
        )
        .execute()
    )

    eval_id = insert.data[0]["id"] if insert.data else None
    return EvalResponse(id=eval_id, metrics=metrics, unsupported_items=unsupported_items)
