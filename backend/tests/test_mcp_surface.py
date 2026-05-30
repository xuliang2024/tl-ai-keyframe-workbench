from fastapi.testclient import TestClient

from app.main import app
from app.mcp.tools import MCP_TOOL_SCHEMAS


def test_mcp_tools_docs_list_registered_tools() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/mcp/tools")

    assert response.status_code == 200
    body = response.json()
    names = {tool["name"] for tool in body["tools"]}
    assert {"project", "script", "asset", "frame", "generate", "get_result"}.issubset(names)
    assert body["total"] == len(MCP_TOOL_SCHEMAS)


def test_mcp_streamable_http_lists_tools() -> None:
    client = TestClient(app)
    init_response = client.post(
        "/api/v1/mcp-http",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )

    assert init_response.status_code == 200
    session_id = init_response.headers["Mcp-Session-Id"]
    assert init_response.json()["result"]["serverInfo"]["name"] == "framelab"

    tools_response = client.post(
        "/api/v1/mcp-http",
        headers={"Mcp-Session-Id": session_id},
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )

    assert tools_response.status_code == 200
    tools = tools_response.json()["result"]["tools"]
    assert any(tool["name"] == "project" for tool in tools)
