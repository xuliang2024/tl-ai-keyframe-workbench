from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.mcp.tools import MCP_TOOL_SCHEMAS, list_tools

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/tools")
async def list_mcp_tools() -> dict:
    return {
        "tools": [
            {
                "name": schema["name"],
                "description": schema["description"],
                "inputSchema": schema["inputSchema"],
            }
            for schema in MCP_TOOL_SCHEMAS.values()
        ],
        "total": len(MCP_TOOL_SCHEMAS),
    }


@router.get("/tools/{tool_name}")
async def get_mcp_tool(tool_name: str) -> dict:
    schema = MCP_TOOL_SCHEMAS.get(tool_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Unknown MCP tool: {tool_name}. Available: {list_tools()}")
    return schema
