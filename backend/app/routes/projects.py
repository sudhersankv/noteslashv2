"""Project API routes."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.db import get_supabase
from app.models.schemas import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    EvalResponse,
    InsightsResponse,
    InsightItem,
    EvidenceItem,
    ProjectCreate,
    ProjectResponse,
    ProjectStatus,
    ReportResponse,
    SampleResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.chat import chat_project, get_chat_history
from app.services.evals import run_evaluation
from app.services.media import is_audio_file
from app.services.pipeline import process_project
from app.services.reports import generate_report
from app.services.search import search_project
from app.services.transcription import transcribe_audio

router = APIRouter(prefix="/api/projects", tags=["projects"])

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "sample-data"


def _get_project_or_404(project_id: UUID) -> dict:
    sb = get_supabase()
    result = sb.table("projects").select("*").eq("id", str(project_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Library not found")
    return result.data[0]


@router.post("", response_model=ProjectResponse)
def create_project(body: ProjectCreate):
    sb = get_supabase()
    result = sb.table("projects").insert({"name": body.name}).execute()
    row = result.data[0]
    return ProjectResponse(id=row["id"], name=row["name"])


@router.post("/sample", response_model=SampleResponse)
def create_sample_project():
    sb = get_supabase()
    result = sb.table("projects").insert({"name": "Sample Library"}).execute()
    project = result.data[0]
    pid = project["id"]

    files = sorted(SAMPLE_DIR.glob("customer_interview_*.txt"))
    if not files:
        raise HTTPException(status_code=500, detail="Sample content not found")

    for f in files:
        sb.table("transcripts").insert(
            {
                "project_id": pid,
                "filename": f.name,
                "raw_text": f.read_text(encoding="utf-8"),
                "status": "pending",
                "media_type": "text",
            }
        ).execute()

    return SampleResponse(project=ProjectResponse(id=project["id"], name=project["name"]))


@router.post("/demo", response_model=SampleResponse, deprecated=True)
def create_demo_project_legacy():
    return create_sample_project()


async def _handle_upload_file(upload: UploadFile, pid: str) -> None:
    if not upload.filename:
        return
    content = await upload.read()
    max_bytes = settings.max_audio_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {settings.max_audio_size_mb}MB)",
        )

    if is_audio_file(upload.filename, upload.content_type):
        text = transcribe_audio(content, upload.filename)
        media_type = "audio"
    else:
        text = content.decode("utf-8", errors="replace")
        media_type = "text"

    if not text.strip():
        raise HTTPException(status_code=400, detail=f"Could not extract text from {upload.filename}")

    sb = get_supabase()
    sb.table("transcripts").insert(
        {
            "project_id": pid,
            "filename": upload.filename,
            "raw_text": text,
            "status": "pending",
            "media_type": media_type,
        }
    ).execute()


@router.post("/{project_id}/upload")
async def upload_transcripts(
    project_id: UUID,
    files: list[UploadFile] = File(default=[]),
    paste_text: str | None = Form(default=None),
):
    _get_project_or_404(project_id)
    pid = str(project_id)
    count = 0

    for upload in files:
        await _handle_upload_file(upload, pid)
        count += 1

    if paste_text and paste_text.strip():
        get_supabase().table("transcripts").insert(
            {
                "project_id": pid,
                "filename": "pasted.txt",
                "raw_text": paste_text.strip(),
                "status": "pending",
                "media_type": "text",
            }
        ).execute()
        count += 1

    if count == 0:
        raise HTTPException(status_code=400, detail="No files or text provided")

    return {"uploaded": count}


@router.post("/{project_id}/process")
def process(project_id: UUID):
    _get_project_or_404(project_id)
    try:
        process_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}") from e
    return {"status": "ready"}


@router.get("/{project_id}/status", response_model=ProjectStatus)
def get_status(project_id: UUID):
    project = _get_project_or_404(project_id)
    sb = get_supabase()
    pid = str(project_id)

    transcripts = sb.table("transcripts").select("status").eq("project_id", pid).execute()
    rows = transcripts.data or []
    transcript_count = len(rows)

    base_tags = project.get("tags") or []
    content_type = project.get("content_type")

    if transcript_count == 0:
        return ProjectStatus(status="empty", transcript_count=0)

    statuses = [r["status"] for r in rows]
    if any(s == "processing" for s in statuses):
        return ProjectStatus(status="processing", transcript_count=transcript_count)
    if any(s == "failed" for s in statuses) and not any(s == "ready" for s in statuses):
        return ProjectStatus(status="failed", transcript_count=transcript_count, message="Processing failed")
    if any(s == "pending" for s in statuses):
        return ProjectStatus(status="pending", transcript_count=transcript_count)

    chunks = sb.table("chunks").select("id", count="exact").eq("project_id", pid).execute()
    insights = sb.table("insights").select("id", count="exact").eq("project_id", pid).execute()
    chunk_count = chunks.count or 0
    insight_count = insights.count or 0

    if chunk_count > 0 and insight_count > 0:
        return ProjectStatus(
            status="ready",
            transcript_count=transcript_count,
            chunk_count=chunk_count,
            insight_count=insight_count,
            content_type=content_type,
            tags=base_tags,
        )

    return ProjectStatus(
        status="pending",
        transcript_count=transcript_count,
        chunk_count=chunk_count,
        insight_count=insight_count,
        content_type=content_type,
        tags=base_tags,
        message="Run process to analyze content",
    )


@router.get("/{project_id}/insights", response_model=InsightsResponse)
def get_insights(project_id: UUID):
    project = _get_project_or_404(project_id)
    sb = get_supabase()
    rows = (
        sb.table("insights")
        .select("*")
        .eq("project_id", str(project_id))
        .order("created_at")
        .execute()
    ).data or []

    themes, pains, features = [], [], []
    for r in rows:
        evidence = [
            EvidenceItem(
                chunk_id=e.get("chunk_id"),
                transcript_id=e.get("transcript_id"),
                filename=e.get("filename"),
                quote=e.get("quote", ""),
            )
            for e in (r.get("evidence") or [])
            if e.get("chunk_id")
        ]
        item = InsightItem(
            id=r["id"],
            type=r["type"],
            title=r["title"],
            description=r.get("description"),
            frequency=r.get("frequency"),
            confidence=float(r["confidence"]) if r.get("confidence") is not None else None,
            evidence=evidence,
        )
        if r["type"] == "theme":
            themes.append(item)
        elif r["type"] == "pain_point":
            pains.append(item)
        elif r["type"] == "feature_request":
            features.append(item)

    content_type = project.get("content_type") or "other"
    summary = themes[0].description if themes and themes[0].description else (
        "Summary of your indexed library content."
    )

    return InsightsResponse(
        summary=summary,
        content_type=content_type,
        tags=project.get("tags") or [],
        themes=themes,
        pain_points=pains,
        feature_requests=features,
    )


@router.post("/{project_id}/search", response_model=SearchResponse)
def search(project_id: UUID, body: SearchRequest):
    _get_project_or_404(project_id)
    chunks = get_supabase().table("chunks").select("id", count="exact").eq("project_id", str(project_id)).execute()
    if not (chunks.count or 0):
        raise HTTPException(status_code=400, detail="Process your library before searching")
    return search_project(project_id, body.query)


@router.post("/{project_id}/chat", response_model=ChatResponse)
def chat(project_id: UUID, body: ChatRequest):
    _get_project_or_404(project_id)
    chunks = get_supabase().table("chunks").select("id", count="exact").eq("project_id", str(project_id)).execute()
    if not (chunks.count or 0):
        raise HTTPException(status_code=400, detail="Process your library before chatting")
    return chat_project(project_id, body.message)


@router.get("/{project_id}/chat", response_model=ChatHistoryResponse)
def chat_history(project_id: UUID):
    _get_project_or_404(project_id)
    return ChatHistoryResponse(messages=get_chat_history(project_id))


@router.post("/{project_id}/evaluate", response_model=EvalResponse)
def evaluate(project_id: UUID):
    _get_project_or_404(project_id)
    insights = get_supabase().table("insights").select("id", count="exact").eq("project_id", str(project_id)).execute()
    if not (insights.count or 0):
        raise HTTPException(status_code=400, detail="No insights to evaluate")
    return run_evaluation(project_id)


@router.get("/{project_id}/evaluate/latest", response_model=EvalResponse)
def get_latest_eval(project_id: UUID):
    _get_project_or_404(project_id)
    sb = get_supabase()
    result = (
        sb.table("eval_runs")
        .select("*")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No evaluation found")
    row = result.data[0]
    from app.models.schemas import EvalMetrics, UnsupportedItem

    metrics = EvalMetrics(**row["metrics"])
    unsupported = [UnsupportedItem(**u) for u in (row.get("unsupported_items") or [])]
    return EvalResponse(id=row["id"], metrics=metrics, unsupported_items=unsupported)


@router.post("/{project_id}/report", response_model=ReportResponse)
def create_report(project_id: UUID):
    _get_project_or_404(project_id)
    markdown = generate_report(project_id)
    latest = (
        get_supabase()
        .table("reports")
        .select("id")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rid = latest.data[0]["id"] if latest.data else None
    return ReportResponse(id=rid, markdown=markdown)


@router.get("/{project_id}/report/latest", response_model=ReportResponse)
def get_latest_report(project_id: UUID):
    _get_project_or_404(project_id)
    result = (
        get_supabase()
        .table("reports")
        .select("*")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No report found")
    row = result.data[0]
    return ReportResponse(id=row["id"], markdown=row["markdown"])
