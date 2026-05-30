from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx


class FrameLabClientError(RuntimeError):
    """Raised when the FrameLab API returns an error response."""


class FrameLabClient:
    """Small Python SDK for FrameLab API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000/api/v1",
        *,
        timeout: float = 60.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "FrameLabClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def list_projects(self) -> list[dict[str, Any]]:
        return self._get("/projects")["items"]

    def create_project(
        self,
        *,
        name: str,
        description: str = "",
        aspect_ratio: str = "16:9",
    ) -> dict[str, Any]:
        return self._post(
            "/projects",
            {"name": name, "description": description, "aspect_ratio": aspect_ratio},
        )

    def get_project(self, project_id: str) -> dict[str, Any]:
        return self._get(f"/projects/{project_id}")

    def update_project(self, project_id: str, **fields: Any) -> dict[str, Any]:
        return self._patch(f"/projects/{project_id}", _drop_none(fields))

    def delete_project(self, project_id: str) -> None:
        self._delete(f"/projects/{project_id}")

    def get_script(self, project_id: str) -> dict[str, Any]:
        return self._get(f"/projects/{project_id}/script")

    def update_script(self, project_id: str, content: str) -> dict[str, Any]:
        return self._put(f"/projects/{project_id}/script", {"content": content})

    def clear_script(self, project_id: str) -> None:
        self._delete(f"/projects/{project_id}/script")

    def list_assets(self, project_id: str) -> list[dict[str, Any]]:
        return self._get(f"/projects/{project_id}/assets")["items"]

    def create_asset(
        self,
        project_id: str,
        *,
        name: str,
        type: str = "other",
        description: str = "",
        default_prompt: str = "",
        tags: list[str] | None = None,
        image_file_id: str | None = None,
        sort_order: int = 0,
    ) -> dict[str, Any]:
        return self._post(
            f"/projects/{project_id}/assets",
            {
                "name": name,
                "type": type,
                "description": description,
                "default_prompt": default_prompt,
                "tags": tags or [],
                "image_file_id": image_file_id,
                "sort_order": sort_order,
            },
        )

    def update_asset(self, asset_id: str, **fields: Any) -> dict[str, Any]:
        return self._patch(f"/assets/{asset_id}", _drop_none(fields))

    def delete_asset(self, asset_id: str) -> None:
        self._delete(f"/assets/{asset_id}")

    def list_frames(self, project_id: str) -> list[dict[str, Any]]:
        return self._get(f"/projects/{project_id}/frames")["items"]

    def create_frame(
        self,
        project_id: str,
        *,
        summary: str = "",
        order_index: int | None = None,
        duration_ms: int = 3000,
        current_prompt: str = "",
    ) -> dict[str, Any]:
        return self._post(
            f"/projects/{project_id}/frames",
            {
                "summary": summary,
                "order_index": order_index,
                "duration_ms": duration_ms,
                "current_prompt": current_prompt,
            },
        )

    def update_frame(self, frame_id: str, **fields: Any) -> dict[str, Any]:
        return self._patch(f"/frames/{frame_id}", _drop_none(fields))

    def delete_frame(self, frame_id: str) -> dict[str, Any]:
        return self._delete(f"/frames/{frame_id}")

    def create_media_upload_url(
        self,
        *,
        filename: str,
        file_type: str,
        mime_type: str,
        size_bytes: int | None = None,
        project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/media/upload-url",
            {
                "filename": filename,
                "file_type": file_type,
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "project_id": project_id,
                "metadata": metadata or {},
            },
        )

    def complete_media_upload(
        self,
        media_file_id: str,
        **metadata: Any,
    ) -> dict[str, Any]:
        return self._post(f"/media/{media_file_id}/complete", _drop_none(metadata))

    def upload_file(
        self,
        path: str | Path,
        *,
        file_type: str,
        mime_type: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        file_path = Path(path)
        upload = self.create_media_upload_url(
            filename=file_path.name,
            file_type=file_type,
            mime_type=mime_type,
            size_bytes=file_path.stat().st_size,
            project_id=project_id,
        )
        with file_path.open("rb") as file_obj:
            response = self._client.request(
                upload["upload_method"],
                upload["upload_url"],
                headers=upload["upload_headers"],
                content=file_obj,
            )
        response.raise_for_status()
        return self.complete_media_upload(upload["media_file_id"], size_bytes=file_path.stat().st_size)

    def create_generation_task(
        self,
        *,
        prompt: str,
        aspect_ratio: str = "16:9",
        task_type: str | None = None,
        image: str | list[str] | None = None,
        size: str | None = None,
        project_id: str | None = None,
        frame_id: str | None = None,
        asset_ids: list[str] | None = None,
        auto_apply_asset_references: bool | None = None,
        image_type: str | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/generation-tasks",
            _drop_none(
                {
                    "task_type": task_type,
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "image": image,
                    "size": size,
                    "project_id": project_id,
                    "frame_id": frame_id,
                    "asset_ids": asset_ids,
                    "auto_apply_asset_references": auto_apply_asset_references,
                    "image_type": image_type,
                }
            ),
        )

    def get_generation_task(self, task_id: str) -> dict[str, Any]:
        return self._get(f"/generation-tasks/{task_id}")

    def retry_generation_task(self, task_id: str) -> dict[str, Any]:
        return self._post(f"/generation-tasks/{task_id}/retry", {})

    def cancel_generation_task(self, task_id: str) -> dict[str, Any]:
        return self._post(f"/generation-tasks/{task_id}/cancel", {})

    def wait_generation_task(
        self,
        task_id: str,
        *,
        interval_seconds: float = 2.0,
        timeout_seconds: float = 600.0,
    ) -> dict[str, Any]:
        started_at = time.monotonic()
        while True:
            task = self.get_generation_task(task_id)
            if task["status"] in {"succeeded", "failed", "canceled"}:
                return task
            if time.monotonic() - started_at > timeout_seconds:
                raise FrameLabClientError(f"Timed out waiting for generation task {task_id}")
            time.sleep(interval_seconds)

    def _get(self, path: str) -> Any:
        return self._request("GET", path)

    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request("POST", path, json=payload)

    def _patch(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request("PATCH", path, json=payload)

    def _put(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request("PUT", path, json=payload)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._client.request(method, f"{self.base_url}{path}", **kwargs)
        if response.status_code >= 400:
            raise FrameLabClientError(_error_message(response))
        if response.status_code == 204 or not response.content:
            return None
        return response.json()


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _error_message(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text
    return f"FrameLab API error {response.status_code}: {detail or response.reason_phrase}"
