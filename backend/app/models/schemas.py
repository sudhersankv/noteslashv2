"""Pydantic request/response schemas."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectResponse(BaseModel):
    id: UUID
    name: str


class ProjectStatus(BaseModel):
    status: Literal["empty", "pending", "processing", "ready", "failed"]
    transcript_count: int = 0
    chunk_count: int = 0
    insight_count: int = 0
    content_type: str | None = None
    tags: list[str] = []
    message: str | None = None


class EvidenceItem(BaseModel):
    chunk_id: UUID
    transcript_id: UUID | None = None
    filename: str | None = None
    quote: str


class InsightItem(BaseModel):
    id: UUID
    type: Literal["theme", "pain_point", "feature_request", "contradiction"]
    title: str
    description: str | None = None
    frequency: int | None = None
    confidence: float | None = None
    evidence: list[EvidenceItem] = []


class InsightsResponse(BaseModel):
    summary: str
    content_type: str | None = None
    tags: list[str] = []
    themes: list[InsightItem] = []
    pain_points: list[InsightItem] = []
    feature_requests: list[InsightItem] = []


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class Citation(BaseModel):
    chunk_id: UUID
    transcript_id: UUID | None = None
    filename: str | None = None
    text: str
    speaker: str | None = None
    similarity: float | None = None


class SearchResponse(BaseModel):
    answer: str
    citations: list[Citation] = []


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageItem(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = []


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    message_id: UUID | None = None


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageItem] = []


class VoiceSessionResponse(BaseModel):
    client_secret: str
    expires_at: int | None = None
    model: str


class VoiceToolRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class VoiceToolResponse(BaseModel):
    snippets: list[dict] = []


class EvalMetrics(BaseModel):
    insights_total: int = 0
    grounded: int = 0
    unsupported: int = 0
    grounding_score: float = 0.0


class UnsupportedItem(BaseModel):
    insight_id: UUID
    insight_title: str
    reason: str


class EvalResponse(BaseModel):
    id: UUID | None = None
    metrics: EvalMetrics
    unsupported_items: list[UnsupportedItem] = []


class ReportResponse(BaseModel):
    id: UUID | None = None
    markdown: str


class SampleResponse(BaseModel):
    project: ProjectResponse
