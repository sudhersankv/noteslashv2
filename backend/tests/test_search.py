import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models.schemas import SearchResponse
from app.services.search import search_project


@patch("app.services.search.retrieve_chunks")
@patch("app.services.search.get_openai")
def test_search_returns_citations(mock_openai, mock_retrieve):
    chunk_id = str(uuid4())
    transcript_id = str(uuid4())
    mock_retrieve.return_value = [
        {
            "id": chunk_id,
            "transcript_id": transcript_id,
            "text": "The setup took me almost two days.",
            "speaker": "Participant",
            "filename": "interview_1.txt",
            "similarity": 0.92,
        }
    ]

    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "answer": "Users struggled with setup.",
                            "cited_chunk_ids": [chunk_id],
                        }
                    )
                )
            )
        ]
    )

    result = search_project(uuid4(), "onboarding")
    assert isinstance(result, SearchResponse)
    assert "setup" in result.answer.lower()
    assert len(result.citations) >= 1
    assert result.citations[0].text == "The setup took me almost two days."
