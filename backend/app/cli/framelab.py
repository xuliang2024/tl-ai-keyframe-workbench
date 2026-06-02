from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from app.sdk import FrameLabClient, FrameLabClientError


DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_BASE_URLS = [
    DEFAULT_BASE_URL,
    "http://127.0.0.1:18081/api/v1",
    "http://127.0.0.1:18080/api/v1",
    "http://127.0.0.1:18082/api/v1",
]
ENV_BASE_URL = "FRAMELAB_API_BASE_URL"
ENV_TOKEN = "FRAMELAB_API_TOKEN"


def main() -> None:
    parser = argparse.ArgumentParser(description="FrameLab CLI")
    parser.add_argument("--base-url", default=os.getenv(ENV_BASE_URL), help=f"API base URL. Defaults to {ENV_BASE_URL} or local auto-detection.")
    parser.add_argument("--token", default=os.getenv(ENV_TOKEN), help=f"API access token. Defaults to {ENV_TOKEN}.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="检查后端健康状态")

    auth = sub.add_parser("auth", help="认证与 token 管理")
    auth_sub = auth.add_subparsers(dest="action")
    auth_register = auth_sub.add_parser("register", help="注册用户并签发网页登录 token")
    auth_register.add_argument("--email", required=True)
    auth_register.add_argument("--username", required=True)
    auth_register.add_argument("--password", required=True)
    auth_register.add_argument("--display-name", default="")
    auth_login = auth_sub.add_parser("login", help="登录并签发网页登录 token")
    auth_login.add_argument("--login", required=True, help="邮箱或用户名")
    auth_login.add_argument("--password", required=True)
    auth_sub.add_parser("me", help="查看当前 token 对应用户")
    auth_refresh = auth_sub.add_parser("refresh", help="使用 refresh token 换新 token")
    auth_refresh.add_argument("--refresh-token", required=True)
    auth_logout = auth_sub.add_parser("logout", help="撤销 refresh token")
    auth_logout.add_argument("--refresh-token", required=True)
    mcp_token = auth_sub.add_parser("mcp-token", help="签发长期 MCP token")
    mcp_token_sub = mcp_token.add_subparsers(dest="mcp_action")
    mcp_token_create = mcp_token_sub.add_parser("create", help="创建长期 MCP token")
    mcp_token_create.add_argument("--name", default="MCP token")
    mcp_token_sub.add_parser("list", help="列出长期 MCP token")
    mcp_token_revoke = mcp_token_sub.add_parser("revoke", help="撤销长期 MCP token")
    mcp_token_revoke.add_argument("token_id")

    projects = sub.add_parser("projects", help="项目管理")
    projects_sub = projects.add_subparsers(dest="action")
    projects_sub.add_parser("list", help="列出项目")
    project_create = projects_sub.add_parser("create", help="创建项目")
    project_create.add_argument("--name", required=True)
    project_create.add_argument("--description", default="")
    project_create.add_argument("--aspect-ratio", default="16:9")
    project_update = projects_sub.add_parser("update", help="更新项目")
    project_update.add_argument("project_id")
    project_update.add_argument("--name")
    project_update.add_argument("--description")
    project_update.add_argument("--aspect-ratio")
    project_update.add_argument("--style-prompt")
    project_update.add_argument("--style-reference-image-file-id")
    project_update.add_argument("--auto-apply-style-prompt", action="store_true")
    project_update.add_argument("--auto-apply-style-reference", action="store_true")
    project_delete = projects_sub.add_parser("delete", help="删除项目")
    project_delete.add_argument("project_id")

    script = sub.add_parser("script", help="剧本管理")
    script_sub = script.add_subparsers(dest="action")
    script_get = script_sub.add_parser("get", help="读取剧本")
    script_get.add_argument("project_id")
    script_set = script_sub.add_parser("set", help="保存剧本")
    script_set.add_argument("project_id")
    script_set.add_argument("--file", type=Path)
    script_set.add_argument("--content")
    script_clear = script_sub.add_parser("clear", help="清空剧本")
    script_clear.add_argument("project_id")

    assets = sub.add_parser("assets", help="资产管理")
    assets_sub = assets.add_subparsers(dest="action")
    assets_list = assets_sub.add_parser("list", help="列出资产")
    assets_list.add_argument("project_id")
    asset_create = assets_sub.add_parser("create", help="创建资产")
    asset_create.add_argument("project_id")
    asset_create.add_argument("--name", required=True)
    asset_create.add_argument("--type", default="other")
    asset_create.add_argument("--description", default="")
    asset_create.add_argument("--prompt", default="")
    asset_update = assets_sub.add_parser("update", help="更新资产")
    asset_update.add_argument("asset_id")
    asset_update.add_argument("--name")
    asset_update.add_argument("--type")
    asset_update.add_argument("--description")
    asset_update.add_argument("--prompt")
    asset_update.add_argument("--image-file-id")
    asset_delete = assets_sub.add_parser("delete", help="删除资产")
    asset_delete.add_argument("asset_id")

    frames = sub.add_parser("frames", help="关键帧管理")
    frames_sub = frames.add_subparsers(dest="action")
    frames_list = frames_sub.add_parser("list", help="列出关键帧")
    frames_list.add_argument("project_id")
    frame_create = frames_sub.add_parser("create", help="创建关键帧")
    frame_create.add_argument("project_id")
    frame_create.add_argument("--summary", default="")
    frame_create.add_argument("--prompt", default="")
    frame_create.add_argument("--duration-ms", type=int, default=3000)
    frame_update = frames_sub.add_parser("update", help="更新关键帧")
    frame_update.add_argument("frame_id")
    frame_update.add_argument("--summary")
    frame_update.add_argument("--prompt")
    frame_update.add_argument("--duration-ms", type=int)
    frame_delete = frames_sub.add_parser("delete", help="删除关键帧")
    frame_delete.add_argument("frame_id")

    generate = sub.add_parser("generate", help="提交生成任务")
    generate.add_argument("--prompt", required=True)
    generate.add_argument("--project-id")
    generate.add_argument("--task-type")
    generate.add_argument("--image-type", choices=["style", "character", "scene", "prop", "keyframe"])
    generate.add_argument("--aspect-ratio", default="16:9")
    generate.add_argument("--frame-id")
    generate.add_argument("--asset-id", action="append", dest="asset_ids")
    generate.add_argument("--no-auto-asset-references", action="store_true")
    generate.add_argument("--image", action="append")
    generate.add_argument("--wait", action="store_true")
    generate.add_argument("--interval", type=float, default=2.0)
    generate.add_argument("--timeout", type=float, default=600.0)

    task = sub.add_parser("task", help="生成任务")
    task_sub = task.add_subparsers(dest="action")
    task_list = task_sub.add_parser("list", help="查询任务列表")
    task_list.add_argument("--status")
    task_list.add_argument("--task-type")
    task_list.add_argument("--project-id")
    task_list.add_argument("--target-type")
    task_list.add_argument("--target-id")
    task_list.add_argument("--limit", type=int, default=50)
    task_get = task_sub.add_parser("get", help="查询任务")
    task_get.add_argument("task_id")
    task_wait = task_sub.add_parser("wait", help="等待任务完成")
    task_wait.add_argument("task_id")
    task_wait.add_argument("--interval", type=float, default=2.0)
    task_wait.add_argument("--timeout", type=float, default=600.0)
    task_cancel = task_sub.add_parser("cancel", help="取消任务")
    task_cancel.add_argument("task_id")
    task_retry = task_sub.add_parser("retry", help="重试任务")
    task_retry.add_argument("task_id")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    try:
        with _open_client(args.base_url, args.token) as client:
            result = _dispatch(client, args)
    except FrameLabClientError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if result is not None:
        _print_json(result)


def _dispatch(client: FrameLabClient, args: argparse.Namespace) -> Any:
    if args.command == "health":
        return client.health()

    if args.command == "auth":
        if args.action == "register":
            return client.register(
                email=args.email,
                username=args.username,
                password=args.password,
                display_name=args.display_name,
            )
        if args.action == "login":
            return client.login(login=args.login, password=args.password)
        if args.action == "me":
            return client.me()
        if args.action == "refresh":
            return client.refresh_token(args.refresh_token)
        if args.action == "logout":
            return client.logout(args.refresh_token)
        if args.action == "mcp-token":
            if args.mcp_action == "create":
                return client.create_mcp_token(name=args.name)
            if args.mcp_action == "list":
                return client.list_mcp_tokens()
            if args.mcp_action == "revoke":
                return client.revoke_mcp_token(args.token_id)

    if args.command == "projects":
        if args.action == "list":
            return client.list_projects()
        if args.action == "create":
            return client.create_project(
                name=args.name,
                description=args.description,
                aspect_ratio=args.aspect_ratio,
            )
        if args.action == "update":
            return client.update_project(
                args.project_id,
                name=args.name,
                description=args.description,
                aspect_ratio=args.aspect_ratio,
                style_prompt=args.style_prompt,
                style_reference_image_file_id=args.style_reference_image_file_id,
                auto_apply_style_prompt=args.auto_apply_style_prompt or None,
                auto_apply_style_reference=args.auto_apply_style_reference or None,
            )
        if args.action == "delete":
            return client.delete_project(args.project_id)

    if args.command == "script":
        if args.action == "get":
            return client.get_script(args.project_id)
        if args.action == "set":
            content = args.content
            if args.file:
                content = args.file.read_text(encoding="utf-8")
            if content is None:
                raise FrameLabClientError("script set requires --content or --file")
            return client.update_script(args.project_id, content)
        if args.action == "clear":
            return client.clear_script(args.project_id)

    if args.command == "assets":
        if args.action == "list":
            return client.list_assets(args.project_id)
        if args.action == "create":
            return client.create_asset(
                args.project_id,
                name=args.name,
                type=args.type,
                description=args.description,
                default_prompt=args.prompt,
            )
        if args.action == "update":
            return client.update_asset(
                args.asset_id,
                name=args.name,
                type=args.type,
                description=args.description,
                default_prompt=args.prompt,
                image_file_id=args.image_file_id,
            )
        if args.action == "delete":
            return client.delete_asset(args.asset_id)

    if args.command == "frames":
        if args.action == "list":
            return client.list_frames(args.project_id)
        if args.action == "create":
            return client.create_frame(
                args.project_id,
                summary=args.summary,
                current_prompt=args.prompt,
                duration_ms=args.duration_ms,
            )
        if args.action == "update":
            return client.update_frame(
                args.frame_id,
                summary=args.summary,
                current_prompt=args.prompt,
                duration_ms=args.duration_ms,
            )
        if args.action == "delete":
            return client.delete_frame(args.frame_id)

    if args.command == "generate":
        image: str | list[str] | None = args.image
        if image and len(image) == 1:
            image = image[0]
        task = client.create_generation_task(
            prompt=args.prompt,
            project_id=args.project_id,
            task_type=args.task_type,
            image_type=args.image_type,
            aspect_ratio=args.aspect_ratio,
            frame_id=args.frame_id,
            asset_ids=args.asset_ids,
            auto_apply_asset_references=False if args.no_auto_asset_references else None,
            image=image,
        )
        if args.wait:
            return client.wait_generation_task(
                task["task_id"],
                interval_seconds=args.interval,
                timeout_seconds=args.timeout,
            )
        return task

    if args.command == "task":
        if args.action == "list":
            return client.list_generation_tasks(
                status=args.status,
                task_type=args.task_type,
                project_id=args.project_id,
                target_type=args.target_type,
                target_id=args.target_id,
                limit=args.limit,
            )
        if args.action == "get":
            return client.get_generation_task(args.task_id)
        if args.action == "wait":
            return client.wait_generation_task(
                args.task_id,
                interval_seconds=args.interval,
                timeout_seconds=args.timeout,
            )
        if args.action == "cancel":
            return client.cancel_generation_task(args.task_id)
        if args.action == "retry":
            return client.retry_generation_task(args.task_id)

    raise FrameLabClientError("Unknown command")


def _open_client(base_url: str | None, token: str | None) -> FrameLabClient:
    if base_url:
        return FrameLabClient(base_url, access_token=token)

    last_error: FrameLabClientError | None = None
    for candidate in DEFAULT_BASE_URLS:
        client = FrameLabClient(candidate, access_token=token)
        try:
            client.health()
            return client
        except FrameLabClientError as exc:
            client.close()
            last_error = exc

    message = str(last_error) if last_error else "No local FrameLab API candidates configured"
    raise FrameLabClientError(
        f"Unable to find a local FrameLab API. Tried: {', '.join(DEFAULT_BASE_URLS)}. Last error: {message}"
    )


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
