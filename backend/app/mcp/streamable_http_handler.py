from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from app.mcp.tools import MCP_TOOL_SCHEMAS, get_tool

router = APIRouter(prefix="/mcp-http", tags=["mcp"])

_sessions: dict[str, datetime] = {}
_SESSION_TTL = timedelta(hours=1)


@router.post("")
async def mcp_streamable_post(
    request: Request,
    mcp_session_id: str | None = Header(default=None, alias="Mcp-Session-Id"),
) -> Response:
    try:
        body = await request.json()
    except Exception as exc:
        return _jsonrpc_error(None, -32700, f"Parse error: {exc}", status_code=400)

    messages = body if isinstance(body, list) else [body]
    session_id = mcp_session_id
    if not session_id and any(message.get("method") == "initialize" for message in messages):
        session_id = _create_session()
    elif not session_id:
        return _jsonrpc_error(None, -32000, "Missing Mcp-Session-Id. Call initialize first.", status_code=400)
    elif not _touch_session(session_id):
        return _jsonrpc_error(None, -32000, "MCP session expired or not found.", status_code=404)

    responses = []
    for message in messages:
        result = await _process_message(message, session_id)
        if result is not None:
            responses.append(result)

    if not responses:
        return Response(status_code=202)

    payload: Any = responses if isinstance(body, list) else responses[0]
    response = JSONResponse(payload)
    response.headers["Mcp-Session-Id"] = session_id
    return response


@router.get("")
async def mcp_streamable_get(
    mcp_session_id: str | None = Header(default=None, alias="Mcp-Session-Id"),
) -> JSONResponse:
    if not mcp_session_id or not _touch_session(mcp_session_id):
        raise HTTPException(status_code=404, detail="MCP session expired or not found")
    return JSONResponse({"status": "ok", "session_id": mcp_session_id})


@router.delete("")
async def mcp_streamable_delete(
    mcp_session_id: str | None = Header(default=None, alias="Mcp-Session-Id"),
) -> Response:
    if mcp_session_id:
        _sessions.pop(mcp_session_id, None)
    return Response(status_code=204)


async def _process_message(message: dict[str, Any], session_id: str) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    if request_id is None:
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "serverInfo": {"name": "framelab", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": schema["name"],
                        "description": schema["description"],
                        "inputSchema": schema["inputSchema"],
                    }
                    for schema in MCP_TOOL_SCHEMAS.values()
                ]
            },
        }

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not tool_name:
            return _error_payload(request_id, -32602, "Missing tool name")
        try:
            result = await get_tool(tool_name)(arguments, context={"session_id": session_id})
        except Exception as exc:
            return _error_payload(request_id, -32603, str(exc))
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ]
            },
        }

    return _error_payload(request_id, -32601, f"Unknown method: {method}")


def _create_session() -> str:
    _cleanup_sessions()
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = datetime.now(UTC)
    return session_id


def _touch_session(session_id: str) -> bool:
    _cleanup_sessions()
    if session_id not in _sessions:
        return False
    _sessions[session_id] = datetime.now(UTC)
    return True


def _cleanup_sessions() -> None:
    expires_before = datetime.now(UTC) - _SESSION_TTL
    for session_id, last_seen in list(_sessions.items()):
        if last_seen < expires_before:
            _sessions.pop(session_id, None)


def _jsonrpc_error(request_id: Any, code: int, message: str, *, status_code: int) -> JSONResponse:
    return JSONResponse(_error_payload(request_id, code, message), status_code=status_code)


def _error_payload(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
