from fastapi.testclient import TestClient

from app.main import app
from app.services.database_store import store


def test_register_login_me_refresh_logout() -> None:
    store.reset()
    client = TestClient(app)

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "Ada@example.com",
            "username": "Ada_User",
            "password": "correct-horse-battery-staple",
            "display_name": "Ada",
        },
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["token_type"] == "bearer"
    assert register_body["access_token"]
    assert register_body["refresh_token"]
    assert register_body["user"]["email"] == "ada@example.com"
    assert register_body["user"]["username"] == "ada_user"

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {register_body['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "ada@example.com"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"login": "ada_user", "password": "correct-horse-battery-staple"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["access_token"]
    assert login_body["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_body["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert refresh_body["access_token"]
    assert refresh_body["refresh_token"] != login_body["refresh_token"]

    reused_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_body["refresh_token"]},
    )
    assert reused_refresh_response.status_code == 401

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_body["refresh_token"]},
    )
    assert logout_response.status_code == 200


def test_register_rejects_duplicate_email_and_username() -> None:
    store.reset()
    client = TestClient(app)
    payload = {
        "email": "sam@example.com",
        "username": "sam",
        "password": "password-1234",
    }

    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
    assert client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "sam2@example.com"},
    ).status_code == 409


def test_me_requires_access_token() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_mcp_token_issue_list_and_revoke() -> None:
    store.reset()
    client = TestClient(app)
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "mcp@example.com",
            "username": "mcp_owner",
            "password": "correct-horse-battery-staple",
        },
    )
    headers = {"Authorization": f"Bearer {register_response.json()['access_token']}"}

    create_response = client.post(
        "/api/v1/auth/mcp-tokens",
        json={"name": "local agent"},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["token"].startswith("mcp_")
    assert created["name"] == "local agent"

    list_response = client.get("/api/v1/auth/mcp-tokens", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == created["id"]
    assert "token" not in list_response.json()[0]

    revoke_response = client.delete(f"/api/v1/auth/mcp-tokens/{created['id']}", headers=headers)
    assert revoke_response.status_code == 204
    assert client.get("/api/v1/auth/mcp-tokens", headers=headers).json() == []
