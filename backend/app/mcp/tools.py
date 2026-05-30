from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from app.api.v1.generation_tasks import _run_generation_task, _task_response
from app.schemas.generation_task import GenerationTaskCreate
from app.services.database_store import store

McpContext = dict[str, Any] | None
McpTool = Callable[[dict[str, Any], McpContext], Awaitable[dict[str, Any]]]


async def project_tool(arguments: dict[str, Any], context: McpContext = None) -> dict[str, Any]:
    action = arguments.get("action", "list")
    if action == "list":
        return _ok(items=[_record_dict(item) for item in await store.list_projects()])
    if action == "get":
        project = await store.get_project(_required(arguments, "project_id"))
        return _ok(project=_record_dict(project)) if project else _not_found("Project not found")
    if action == "create":
        project = await store.create_project(
            name=_required(arguments, "name"),
            description=arguments.get("description", ""),
            aspect_ratio=arguments.get("aspect_ratio", "16:9"),
        )
        return _ok(project=_record_dict(project))
    if action == "update":
        project = await store.update_project(
            _required(arguments, "project_id"),
            _allowed_fields(
                arguments,
                {
                    "name",
                    "description",
                    "aspect_ratio",
                    "status",
                    "style_prompt",
                    "style_reference_image_file_id",
                    "auto_apply_style_prompt",
                    "auto_apply_style_reference",
                },
            ),
        )
        return _ok(project=_record_dict(project)) if project else _not_found("Project not found")
    if action == "delete":
        deleted = await store.delete_project(_required(arguments, "project_id"))
        return _ok(deleted=deleted) if deleted else _not_found("Project not found")
    return _bad_action(action)


async def script_tool(arguments: dict[str, Any], context: McpContext = None) -> dict[str, Any]:
    action = arguments.get("action", "get")
    project_id = _required(arguments, "project_id")
    if action == "get":
        script = await store.get_script(project_id)
        return _ok(script=_record_dict(script)) if script else _not_found("Project script not found")
    if action in {"set", "update"}:
        script = await store.update_script(project_id, arguments.get("content", ""))
        return _ok(script=_record_dict(script)) if script else _not_found("Project not found")
    if action == "clear":
        script = await store.clear_script(project_id)
        return _ok(script=_record_dict(script)) if script else _not_found("Project not found")
    return _bad_action(action)


async def asset_tool(arguments: dict[str, Any], context: McpContext = None) -> dict[str, Any]:
    action = arguments.get("action", "list")
    if action == "list":
        project_id = _required(arguments, "project_id")
        if not await store.get_project(project_id):
            return _not_found("Project not found")
        return _ok(items=[_record_dict(item) for item in await store.list_assets(project_id)])
    if action == "create":
        asset = await store.create_asset(
            project_id=_required(arguments, "project_id"),
            name=_required(arguments, "name"),
            type=arguments.get("type", "other"),
            description=arguments.get("description", ""),
            default_prompt=arguments.get("default_prompt", arguments.get("prompt", "")),
            tags=arguments.get("tags", []),
            image_file_id=arguments.get("image_file_id"),
            sort_order=arguments.get("sort_order", 0),
        )
        return _ok(asset=_record_dict(asset)) if asset else _not_found("Project not found")
    if action == "update":
        asset = await store.update_asset(
            _required(arguments, "asset_id"),
            _allowed_fields(
                arguments,
                {"name", "type", "description", "default_prompt", "tags", "image_file_id", "sort_order"},
            ),
        )
        return _ok(asset=_record_dict(asset)) if asset else _not_found("Asset not found")
    if action == "delete":
        deleted = await store.delete_asset(_required(arguments, "asset_id"))
        return _ok(deleted=deleted) if deleted else _not_found("Asset not found")
    return _bad_action(action)


async def frame_tool(arguments: dict[str, Any], context: McpContext = None) -> dict[str, Any]:
    action = arguments.get("action", "list")
    if action == "list":
        project_id = _required(arguments, "project_id")
        if not await store.get_project(project_id):
            return _not_found("Project not found")
        return _ok(items=[_record_dict(item) for item in await store.list_frames(project_id)])
    if action == "create":
        frame = await store.create_frame(
            project_id=_required(arguments, "project_id"),
            summary=arguments.get("summary", ""),
            order_index=arguments.get("order_index"),
            duration_ms=arguments.get("duration_ms", 3000),
            current_prompt=arguments.get("current_prompt", arguments.get("prompt", "")),
        )
        return _ok(frame=_record_dict(frame)) if frame else _not_found("Project not found")
    if action == "update":
        frame = await store.update_frame(
            _required(arguments, "frame_id"),
            _allowed_fields(
                arguments,
                {
                    "summary",
                    "duration_ms",
                    "people",
                    "dialogue",
                    "action",
                    "emotion",
                    "note",
                    "current_prompt",
                    "selected_version_id",
                },
            ),
        )
        return _ok(frame=_record_dict(frame)) if frame else _not_found("Frame not found")
    if action == "delete":
        deleted = await store.delete_frame(_required(arguments, "frame_id"))
        return _ok(deleted=deleted) if deleted else _not_found("Frame not found")
    return _bad_action(action)


async def generate_tool(arguments: dict[str, Any], context: McpContext = None) -> dict[str, Any]:
    try:
        payload = GenerationTaskCreate(
            task_type=arguments.get("task_type"),
            prompt=_required(arguments, "prompt"),
            aspect_ratio=arguments.get("aspect_ratio", "16:9"),
            image=arguments.get("image") or arguments.get("images"),
            size=arguments.get("size"),
            project_id=arguments.get("project_id"),
            frame_id=arguments.get("frame_id"),
            asset_ids=arguments.get("asset_ids"),
            auto_apply_asset_references=arguments.get("auto_apply_asset_references", True),
            image_type=arguments.get("image_type"),
        )
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    from app.api.v1.generation_tasks import _model_name_for_task, _prepare_generation_request
    from app.core.config import settings

    try:
        prepared = await _prepare_generation_request(payload)
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    task = await store.create_generation_task(
        provider="apiz",
        task_type=prepared.task_type,
        model_name=_model_name_for_task(prepared.task_type),
        prompt=prepared.prompt,
        aspect_ratio=prepared.payload.aspect_ratio,
        size=prepared.payload.size or settings.image_generation_size,
        request_payload=prepared.request_payload,
    )
    asyncio.create_task(_run_generation_task(task.id))
    return _ok(task=_jsonable(_task_response(task)))


async def get_result_tool(arguments: dict[str, Any], context: McpContext = None) -> dict[str, Any]:
    task_id = _required(arguments, "task_id")
    task = await store.get_generation_task(task_id)
    return _ok(task=_jsonable(_task_response(task))) if task else _not_found("Generation task not found")


async def media_tool(arguments: dict[str, Any], context: McpContext = None) -> dict[str, Any]:
    action = arguments.get("action", "get")
    if action == "get":
        media_file = await store.get_media_file(_required(arguments, "media_file_id"))
        return _ok(media_file=_record_dict(media_file)) if media_file else _not_found("Media file not found")
    return {
        "success": False,
        "error": "Only action=get is available in MCP v1. Use REST/SDK upload flow for local files.",
    }


MCP_TOOLS: dict[str, McpTool] = {
    "project": project_tool,
    "script": script_tool,
    "asset": asset_tool,
    "frame": frame_tool,
    "generate": generate_tool,
    "get_result": get_result_tool,
    "media": media_tool,
}


def get_tool(tool_name: str) -> McpTool:
    tool = MCP_TOOLS.get(tool_name)
    if not tool:
        raise ValueError(f"Unknown MCP tool: {tool_name}")
    return tool


def list_tools() -> list[str]:
    return list(MCP_TOOLS)


MCP_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "project": {
        "name": "project",
        "description": "项目管理：list/get/create/update/delete。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "get", "create", "update", "delete"]},
                "project_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "aspect_ratio": {"type": "string", "default": "16:9"},
                "style_prompt": {"type": "string"},
                "style_reference_image_file_id": {"type": "string"},
                "auto_apply_style_prompt": {"type": "boolean"},
                "auto_apply_style_reference": {"type": "boolean"},
            },
        },
    },
    "script": {
        "name": "script",
        "description": "剧本管理：get/set/clear。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get", "set", "update", "clear"]},
                "project_id": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["project_id"],
        },
    },
    "asset": {
        "name": "asset",
        "description": "资产库管理：list/create/update/delete。可维护角色、场景、道具等资产。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete"]},
                "project_id": {"type": "string"},
                "asset_id": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "description": {"type": "string"},
                "default_prompt": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "image_file_id": {"type": "string"},
                "sort_order": {"type": "integer"},
            },
        },
    },
    "frame": {
        "name": "frame",
        "description": "关键帧管理：list/create/update/delete。版本持久化会在后续后端表结构补齐。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "create", "update", "delete"]},
                "project_id": {"type": "string"},
                "frame_id": {"type": "string"},
                "summary": {"type": "string"},
                "current_prompt": {"type": "string"},
                "duration_ms": {"type": "integer"},
                "people": {"type": "string"},
                "dialogue": {"type": "string"},
                "action_text": {"type": "string", "description": "Use action field in update payload if calling raw API."},
                "emotion": {"type": "string"},
                "note": {"type": "string"},
            },
        },
    },
    "generate": {
        "name": "generate",
        "description": "提交图片/视频生成任务，返回 task_id。使用 get_result 轮询结果。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "project_id": {"type": "string"},
                "image_type": {
                    "type": "string",
                    "enum": ["style", "character", "scene", "prop", "keyframe"],
                    "description": "图片类型。工具会按该类型自动应用 FrameLab 图片生成要求。",
                },
                "task_type": {
                    "type": "string",
                    "enum": ["text_to_image", "image_to_image", "image_edit", "text_to_video", "frames_to_video"],
                },
                "aspect_ratio": {"type": "string", "default": "16:9"},
                "frame_id": {
                    "type": "string",
                    "description": "关键帧 ID。image_type=keyframe 时会用它解析项目并自动带入项目资产参考图。",
                },
                "asset_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "显式指定要作为参考图的资产 ID。未指定时，keyframe 会使用项目已有资产图。",
                },
                "auto_apply_asset_references": {
                    "type": "boolean",
                    "default": True,
                    "description": "keyframe 是否自动附加角色、道具、场景资产参考图。",
                },
                "image": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ]
                },
                "size": {"type": "string"},
            },
            "required": ["prompt"],
        },
    },
    "get_result": {
        "name": "get_result",
        "description": "查询生成任务状态和结果。",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    "media": {
        "name": "media",
        "description": "媒体文件读取。上传请使用 SDK/REST 的 upload-url + complete 流程。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get"]},
                "media_file_id": {"type": "string"},
            },
            "required": ["media_file_id"],
        },
    },
}


def _ok(**payload: Any) -> dict[str, Any]:
    return {"success": True, **payload}


def _not_found(message: str) -> dict[str, Any]:
    return {"success": False, "error": message}


def _bad_action(action: Any) -> dict[str, Any]:
    return {"success": False, "error": f"Unknown action: {action}"}


def _required(arguments: dict[str, Any], key: str) -> Any:
    value = arguments.get(key)
    if value is None or value == "":
        raise ValueError(f"Missing required argument: {key}")
    return value


def _allowed_fields(arguments: dict[str, Any], names: set[str]) -> dict[str, Any]:
    return {key: arguments[key] for key in names if key in arguments and arguments[key] is not None}


def _record_dict(record: Any) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        key: _jsonable(value)
        for key, value in vars(record).items()
        if not key.startswith("_")
    }


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
