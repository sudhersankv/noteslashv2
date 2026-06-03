"""OpenAI embeddings."""

from __future__ import annotations

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def get_openai() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = get_openai()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]
