import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.chat import chat_project


@patch("app.services.chat.retrieve_chunks")
@patch("app.services.chat.get_openai")
@patch("app.services.chat.get_supabase")
def test_chat_returns_answer(mock_sb, mock_openai, mock_retrieve):
    pid = uuid4()
    chunk_id = str(uuid4())
    mock_retrieve.return_value = [
        {
            "id": chunk_id,
            "transcript_id": str(uuid4()),
            "text": "The main topic was pricing.",
            "filename": "ep1.mp3",
            "similarity": 0.9,
        }
    ]

    sb = MagicMock()
    mock_sb.return_value = sb
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": str(uuid4())}])
    sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"role": "user", "content": "What was discussed?"}]
    )

    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "answer": "Pricing was a main topic.",
                            "cited_chunk_ids": [chunk_id],
                        }
                    )
                )
            )
        ]
    )

    result = chat_project(pid, "What was discussed?")
    assert "pricing" in result.answer.lower()
    assert len(result.citations) >= 1
