"""Report generation."""

from __future__ import annotations

from uuid import UUID

from app.agents.prompts import REPORT_SYSTEM, REPORT_USER_TEMPLATE
from app.config import settings
from app.db import get_supabase
from app.services.embedding import get_openai


def generate_report(project_id: UUID) -> str:
    sb = get_supabase()
    project_row = sb.table("projects").select("name, content_type").eq("id", str(project_id)).execute()
    name = project_row.data[0]["name"] if project_row.data else "Library"
    content_type = project_row.data[0].get("content_type") or "other" if project_row.data else "other"

    insights = (
        sb.table("insights")
        .select("*")
        .eq("project_id", str(project_id))
        .execute()
    ).data or []

    themes, pains, features = [], [], []
    for ins in insights:
        line = f"- **{ins['title']}** ({ins.get('frequency') or '?'} mentions): {ins.get('description') or ''}"
        if ins["type"] == "theme":
            themes.append(line)
        elif ins["type"] == "pain_point":
            pains.append(line)
        elif ins["type"] == "feature_request":
            features.append(line)

    summary_insight = next((i for i in insights if i["type"] == "theme"), None)
    summary = summary_insight["description"] if summary_insight else "Customer interview synthesis."

    chunks = (
        sb.table("chunks")
        .select("text, transcript_id")
        .eq("project_id", str(project_id))
        .limit(15)
        .execute()
    ).data or []

    tids = list({c["transcript_id"] for c in chunks})
    tr_rows = (
        sb.table("transcripts").select("id, filename").in_("id", tids).execute()
    ).data or [] if tids else []
    fn_map = {t["id"]: t.get("filename") or "transcript" for t in tr_rows}

    quotes_lines = []
    for c in chunks[:10]:
        fn = fn_map.get(c["transcript_id"], "transcript")
        quotes_lines.append(f'- [{fn}] "{c["text"][:200]}..."')

    client = get_openai()
    user_msg = REPORT_USER_TEMPLATE.format(
        project_name=name,
        content_type=content_type,
        summary=summary,
        themes_text="\n".join(themes) or "None identified",
        pains_text="\n".join(pains) or "None identified",
        features_text="\n".join(features) or "None identified",
        quotes_text="\n".join(quotes_lines) or "No quotes",
    )
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": REPORT_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
    )
    markdown = response.choices[0].message.content or "# Report\n\nUnable to generate."

    sb.table("reports").insert(
        {"project_id": str(project_id), "markdown": markdown}
    ).execute()

    return markdown
