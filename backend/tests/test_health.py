from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cli_installer_script() -> None:
    client = TestClient(app)
    response = client.get("/cli")

    assert response.status_code == 200
    assert "curl -fsSL http://127.0.0.1:18081/cli | sh -s -- --token TOKEN" in response.text
    assert "FRAMELAB_API_URL" in response.text
    assert 'CLIENT="auto"' in response.text
    assert "codex mcp add framelab" in response.text
