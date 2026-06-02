import os

from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = (
    "mysql+asyncmy://keyframe_user:keyframe_pass_51sut@127.0.0.1:3306/"
    "keyframe_workbench_test?charset=utf8mb4"
)


def auth_headers(client: TestClient, *, username: str = "test_user") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "correct-horse-battery-staple",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def mcp_auth_headers(client: TestClient, *, username: str = "mcp_user") -> dict[str, str]:
    headers = auth_headers(client, username=username)
    response = client.post(
        "/api/v1/auth/mcp-tokens",
        json={"name": "test mcp token"},
        headers=headers,
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}"}
