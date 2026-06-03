from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


@patch("app.routes.voice.create_realtime_session")
@patch("app.routes.voice._get_project_or_404")
@patch("app.routes.voice.get_supabase")
def test_voice_session_returns_secret(mock_sb, mock_get_project, mock_session):
    pid = uuid4()
    mock_get_project.return_value = {"id": str(pid), "name": "Test Library"}
    sb = mock_sb.return_value
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(count=5)

    mock_session.return_value = {
        "value": "ek_test_secret",
        "expires_at": 123,
        "session": {"model": "gpt-realtime"},
    }

    client = TestClient(app)
    response = client.post(f"/api/projects/{pid}/voice/session")
    assert response.status_code == 200
    assert response.json()["client_secret"] == "ek_test_secret"
