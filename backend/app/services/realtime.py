"""OpenAI Realtime session creation (GA client_secrets API)."""

from __future__ import annotations

from uuid import UUID

import httpx

from app.config import settings

REALTIME_CLIENT_SECRETS_URL = "https://api.openai.com/v1/realtime/client_secrets"

NOTESLASH_VOICE_INSTRUCTIONS = """You are Noteslash, a voice assistant for the user's personal audio library.
Always use the search_library tool before answering factual questions about the content.
Ground answers in retrieved snippets. Be concise and conversational.
If nothing relevant is found, say so honestly."""


def create_realtime_session(project_id: UUID, project_name: str) -> dict:
    payload = {
        "session": {
            "type": "realtime",
            "model": settings.openai_realtime_model,
            "instructions": (
                f"{NOTESLASH_VOICE_INSTRUCTIONS}\n"
                f"Library name: {project_name}\n"
                f"Library id: {project_id}"
            ),
            "audio": {
                "output": {"voice": settings.openai_tts_voice},
            },
            "tools": [
                {
                    "type": "function",
                    "name": "search_library",
                    "description": "Search the user's indexed audio/text library for relevant passages.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query about the library content",
                            }
                        },
                        "required": ["query"],
                    },
                }
            ],
            "tool_choice": "auto",
        }
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            REALTIME_CLIENT_SECRETS_URL,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()
