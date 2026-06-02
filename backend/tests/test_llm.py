from fastapi.testclient import TestClient

from app.main import app


def test_llm_config() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/llm/config")

    assert response.status_code == 200
    body = response.json()
    assert body["base_url"] == "https://codex.apiz.ai/v1"
    assert body["model"] == "GPT-5.5"


def test_llm_chat_requires_prompt_or_messages() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/llm/chat", json={})

    assert response.status_code == 422
