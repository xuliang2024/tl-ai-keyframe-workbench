from fastapi.testclient import TestClient

from app.main import app
from app.mcp.tools import MCP_TOOL_SCHEMAS
from app.services.database_store import store
from conftest import mcp_auth_headers


def test_mcp_tools_docs_list_registered_tools() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/mcp/tools")

    assert response.status_code == 200
    body = response.json()
    names = {tool["name"] for tool in body["tools"]}
    assert {"project", "script", "asset", "frame", "generate", "get_result"}.issubset(names)
    assert body["total"] == len(MCP_TOOL_SCHEMAS)


def test_mcp_streamable_http_lists_tools() -> None:
    store.reset()
    client = TestClient(app)
    headers = mcp_auth_headers(client)
    init_response = client.post(
        "/api/v1/mcp-http",
        headers=headers,
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )

    assert init_response.status_code == 200
    session_id = init_response.headers["Mcp-Session-Id"]
    assert init_response.json()["result"]["serverInfo"]["name"] == "framelab"

    tools_response = client.post(
        "/api/v1/mcp-http",
        headers={**headers, "Mcp-Session-Id": session_id},
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )

    assert tools_response.status_code == 200
    tools = tools_response.json()["result"]["tools"]
    assert any(tool["name"] == "project" for tool in tools)


def test_mcp_streamable_http_requires_mcp_token() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/mcp-http",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )

    assert response.status_code == 401


def test_mcp_tool_calls_are_scoped_to_token_user() -> None:
    store.reset()
    client = TestClient(app)
    user_a_headers = mcp_auth_headers(client, username="mcp_owner_a")
    user_b_headers = mcp_auth_headers(client, username="mcp_owner_b")

    init_response = client.post(
        "/api/v1/mcp-http",
        headers=user_a_headers,
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )
    session_id = init_response.headers["Mcp-Session-Id"]
    create_response = client.post(
        "/api/v1/mcp-http",
        headers={**user_a_headers, "Mcp-Session-Id": session_id},
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "project",
                "arguments": {"action": "create", "name": "Owner A Project"},
            },
        },
    )
    assert create_response.status_code == 200

    init_b_response = client.post(
        "/api/v1/mcp-http",
        headers=user_b_headers,
        json={"jsonrpc": "2.0", "id": 3, "method": "initialize"},
    )
    session_b_id = init_b_response.headers["Mcp-Session-Id"]
    list_b_response = client.post(
        "/api/v1/mcp-http",
        headers={**user_b_headers, "Mcp-Session-Id": session_b_id},
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "project", "arguments": {"action": "list"}},
        },
    )
    assert list_b_response.status_code == 200
    content = list_b_response.json()["result"]["content"][0]["text"]
    assert "Owner A Project" not in content
