from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class ProjectRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    aspect_ratio: str = "16:9"
    status: str = "active"
    style_prompt: str = ""
    style_reference_image_file_id: str | None = None
    auto_apply_style_prompt: bool = False
    auto_apply_style_reference: bool = False
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class ScriptRecord(BaseModel):
    project_id: str
    content: str = ""
    updated_at: str = Field(default_factory=utc_now)


class FrameRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    order_index: int
    summary: str = ""
    duration_ms: int = 3000
    people: str = ""
    dialogue: str = ""
    action: str = ""
    emotion: str = ""
    note: str = ""
    current_prompt: str = ""
    selected_version_id: str | None = None
    versions: list["FrameVersionRecord"] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class FrameVersionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    frame_id: str
    version_no: int
    image_file_id: str | None = None
    image_url: str | None = None
    generation_task_id: str | None = None
    prompt: str = ""
    note: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class AssetRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    type: str = "other"
    name: str
    description: str = ""
    default_prompt: str = ""
    tags: list[str] = Field(default_factory=list)
    image_file_id: str | None = None
    sort_order: int = 0
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class MediaFileRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str | None = None
    file_type: str
    bucket: str
    object_key: str
    url: str
    mime_type: str
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    size_bytes: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class GenerationTaskRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = "queued"
    task_type: str
    provider: str = "volcengine_ark"
    model_name: str
    prompt: str
    aspect_ratio: str
    size: str
    request_payload: dict[str, Any] = Field(default_factory=dict)
    images: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] | None = None
    response_payload: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class MemoryStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.projects: dict[str, ProjectRecord] = {}
        self.scripts: dict[str, ScriptRecord] = {}
        self.frames: dict[str, FrameRecord] = {}
        self.frame_versions: dict[str, FrameVersionRecord] = {}
        self.assets: dict[str, AssetRecord] = {}
        self.media_files: dict[str, MediaFileRecord] = {}
        self.generation_tasks: dict[str, GenerationTaskRecord] = {}

    def create_project(
        self,
        name: str,
        description: str = "",
        aspect_ratio: str = "16:9",
    ) -> ProjectRecord:
        project = ProjectRecord(name=name, description=description, aspect_ratio=aspect_ratio)
        self.projects[project.id] = project
        self.scripts[project.id] = ScriptRecord(project_id=project.id)
        self.create_frame(project.id, summary="首个关键帧", order_index=1)
        return project

    def list_projects(self) -> list[ProjectRecord]:
        return sorted(self.projects.values(), key=lambda project: project.created_at, reverse=True)

    def get_project(self, project_id: str) -> ProjectRecord | None:
        return self.projects.get(project_id)

    def update_project(self, project_id: str, values: dict[str, object]) -> ProjectRecord | None:
        project = self.projects.get(project_id)
        if not project:
            return None

        update_values = {key: value for key, value in values.items() if value is not None}
        update_values["updated_at"] = utc_now()
        updated = project.model_copy(update=update_values)
        self.projects[project_id] = updated
        return updated

    def delete_project(self, project_id: str) -> bool:
        if project_id not in self.projects:
            return False

        self.projects.pop(project_id)
        self.scripts.pop(project_id, None)
        self.frames = {
            frame_id: frame for frame_id, frame in self.frames.items() if frame.project_id != project_id
        }
        self.frame_versions = {
            version_id: version
            for version_id, version in self.frame_versions.items()
            if version.frame_id in self.frames
        }
        self.assets = {
            asset_id: asset for asset_id, asset in self.assets.items() if asset.project_id != project_id
        }
        self.media_files = {
            file_id: media
            for file_id, media in self.media_files.items()
            if media.project_id != project_id
        }
        return True

    def get_script(self, project_id: str) -> ScriptRecord | None:
        return self.scripts.get(project_id)

    def update_script(self, project_id: str, content: str) -> ScriptRecord | None:
        if project_id not in self.projects:
            return None
        script = ScriptRecord(project_id=project_id, content=content)
        self.scripts[project_id] = script
        self.projects[project_id].updated_at = utc_now()
        return script

    def clear_script(self, project_id: str) -> ScriptRecord | None:
        return self.update_script(project_id, "")

    def list_frames(self, project_id: str) -> list[FrameRecord]:
        frames = sorted(
            (frame for frame in self.frames.values() if frame.project_id == project_id),
            key=lambda frame: frame.order_index,
        )
        return [self._with_versions(frame) for frame in frames]

    def create_frame(
        self,
        project_id: str,
        summary: str = "",
        order_index: int | None = None,
        duration_ms: int = 3000,
        current_prompt: str = "",
    ) -> FrameRecord | None:
        if project_id not in self.projects:
            return None

        if order_index is None:
            order_index = len(self.list_frames(project_id)) + 1

        frame = FrameRecord(
            project_id=project_id,
            order_index=order_index,
            summary=summary,
            duration_ms=duration_ms,
            current_prompt=current_prompt,
        )
        self.frames[frame.id] = frame
        self.projects[project_id].updated_at = utc_now()
        return frame

    def update_frame(self, frame_id: str, values: dict[str, object]) -> FrameRecord | None:
        frame = self.frames.get(frame_id)
        if not frame:
            return None

        update_values = {**values, "updated_at": utc_now()}
        updated = frame.model_copy(update=update_values)
        self.frames[frame_id] = updated
        self.projects[updated.project_id].updated_at = utc_now()
        return updated

    def delete_frame(self, frame_id: str) -> bool:
        frame = self.frames.pop(frame_id, None)
        if not frame:
            return False
        self.projects[frame.project_id].updated_at = utc_now()
        self.frame_versions = {
            version_id: version
            for version_id, version in self.frame_versions.items()
            if version.frame_id != frame_id
        }
        return True

    def get_frame(self, frame_id: str) -> FrameRecord | None:
        frame = self.frames.get(frame_id)
        return self._with_versions(frame) if frame else None

    def list_frame_versions(self, frame_id: str) -> list[FrameVersionRecord]:
        return sorted(
            (version for version in self.frame_versions.values() if version.frame_id == frame_id),
            key=lambda version: version.version_no,
        )

    def create_frame_version(
        self,
        *,
        frame_id: str,
        image_file_id: str | None = None,
        generation_task_id: str | None = None,
        prompt: str = "",
        note: str = "",
        metadata: dict[str, Any] | None = None,
        select: bool = True,
    ) -> FrameVersionRecord | None:
        frame = self.frames.get(frame_id)
        if not frame:
            return None

        image_url = None
        if image_file_id:
            media_file = self.media_files.get(image_file_id)
            if not media_file:
                return None
            image_url = media_file.url
        if generation_task_id and generation_task_id not in self.generation_tasks:
            return None

        version = FrameVersionRecord(
            frame_id=frame_id,
            version_no=len(self.list_frame_versions(frame_id)) + 1,
            image_file_id=image_file_id,
            image_url=image_url,
            generation_task_id=generation_task_id,
            prompt=prompt,
            note=note,
            metadata=metadata or {},
        )
        self.frame_versions[version.id] = version
        if select:
            self.update_frame(
                frame_id,
                {
                    "selected_version_id": version.id,
                    "current_prompt": prompt or frame.current_prompt,
                    "summary": frame.summary or note or prompt,
                },
            )
        return version

    def select_frame_version(self, frame_id: str, version_id: str) -> FrameRecord | None:
        frame = self.frames.get(frame_id)
        version = self.frame_versions.get(version_id)
        if not frame or not version or version.frame_id != frame_id:
            return None
        return self.update_frame(frame_id, {"selected_version_id": version_id})

    def _with_versions(self, frame: FrameRecord) -> FrameRecord:
        return frame.model_copy(update={"versions": self.list_frame_versions(frame.id)})

    def list_assets(self, project_id: str) -> list[AssetRecord]:
        return sorted(
            (asset for asset in self.assets.values() if asset.project_id == project_id),
            key=lambda asset: (asset.sort_order, asset.created_at),
        )

    def create_asset(
        self,
        project_id: str,
        name: str,
        type: str = "other",
        description: str = "",
        default_prompt: str = "",
        tags: list[str] | None = None,
        image_file_id: str | None = None,
        sort_order: int = 0,
    ) -> AssetRecord | None:
        if project_id not in self.projects:
            return None
        asset = AssetRecord(
            project_id=project_id,
            name=name,
            type=type,
            description=description,
            default_prompt=default_prompt,
            tags=tags or [],
            image_file_id=image_file_id,
            sort_order=sort_order,
        )
        self.assets[asset.id] = asset
        self.projects[project_id].updated_at = utc_now()
        return asset

    def update_asset(self, asset_id: str, values: dict[str, object]) -> AssetRecord | None:
        asset = self.assets.get(asset_id)
        if not asset:
            return None

        update_values = {key: value for key, value in values.items() if value is not None}
        update_values["updated_at"] = utc_now()
        updated = asset.model_copy(update=update_values)
        self.assets[asset_id] = updated
        self.projects[updated.project_id].updated_at = utc_now()
        return updated

    def delete_asset(self, asset_id: str) -> bool:
        asset = self.assets.pop(asset_id, None)
        if not asset:
            return False
        self.projects[asset.project_id].updated_at = utc_now()
        return True

    def create_media_file(
        self,
        *,
        project_id: str | None,
        file_type: str,
        bucket: str,
        object_key: str,
        url: str,
        mime_type: str,
        size_bytes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MediaFileRecord | None:
        if project_id is not None and project_id not in self.projects:
            return None

        media_file = MediaFileRecord(
            project_id=project_id,
            file_type=file_type,
            bucket=bucket,
            object_key=object_key,
            url=url,
            mime_type=mime_type,
            size_bytes=size_bytes,
            metadata=metadata or {},
        )
        self.media_files[media_file.id] = media_file
        if project_id:
            self.projects[project_id].updated_at = utc_now()
        return media_file

    def get_media_file(self, media_file_id: str) -> MediaFileRecord | None:
        return self.media_files.get(media_file_id)

    def complete_media_file(
        self,
        media_file_id: str,
        *,
        width: int | None = None,
        height: int | None = None,
        duration_ms: int | None = None,
        size_bytes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MediaFileRecord | None:
        media_file = self.media_files.get(media_file_id)
        if not media_file:
            return None

        update_values: dict[str, Any] = {
            "status": "uploaded",
            "updated_at": utc_now(),
            "metadata": {**media_file.metadata, **(metadata or {})},
        }
        if width is not None:
            update_values["width"] = width
        if height is not None:
            update_values["height"] = height
        if duration_ms is not None:
            update_values["duration_ms"] = duration_ms
        if size_bytes is not None:
            update_values["size_bytes"] = size_bytes

        updated = media_file.model_copy(update=update_values)
        self.media_files[media_file_id] = updated
        if updated.project_id:
            self.projects[updated.project_id].updated_at = utc_now()
        return updated

    def create_generation_task(
        self,
        *,
        provider: str = "volcengine_ark",
        task_type: str,
        model_name: str,
        prompt: str,
        aspect_ratio: str,
        size: str,
        request_payload: dict[str, Any],
    ) -> GenerationTaskRecord:
        task = GenerationTaskRecord(
            provider=provider,
            task_type=task_type,
            model_name=model_name,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            size=size,
            request_payload=request_payload,
        )
        self.generation_tasks[task.id] = task
        return task

    def get_generation_task(self, task_id: str) -> GenerationTaskRecord | None:
        return self.generation_tasks.get(task_id)

    def update_generation_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        images: list[dict[str, Any]] | None = None,
        usage: dict[str, Any] | None = None,
        response_payload: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> GenerationTaskRecord | None:
        task = self.generation_tasks.get(task_id)
        if not task:
            return None

        update_values: dict[str, Any] = {"updated_at": utc_now()}
        if status is not None:
            update_values["status"] = status
        if images is not None:
            update_values["images"] = images
        if usage is not None:
            update_values["usage"] = usage
        if response_payload is not None:
            update_values["response_payload"] = response_payload
        if error_message is not None:
            update_values["error_message"] = error_message

        updated = task.model_copy(update=update_values)
        self.generation_tasks[task_id] = updated
        return updated


store = MemoryStore()
