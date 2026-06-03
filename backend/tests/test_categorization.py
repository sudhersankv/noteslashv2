import json
from unittest.mock import MagicMock, patch

from app.services.categorization import categorize_text, VALID_TYPES


@patch("app.services.categorization.get_openai")
def test_categorize_returns_valid_type(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "content_type": "podcast",
                            "title_guess": "Startup Stories",
                            "tags": ["startups"],
                            "summary": "A podcast about founders.",
                        }
                    )
                )
            )
        ]
    )
    result = categorize_text("Today we talk about pricing strategies for SaaS...", "ep1.mp3")
    assert result["content_type"] in VALID_TYPES
    assert result["content_type"] == "podcast"
