import asyncio
import json
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.services.memory_store import (
    AssetRecord,
    FrameRecord,
    FrameVersionRecord,
    GenerationTaskRecord,
    MediaFileRecord,
    ProjectRecord,
    ScriptRecord,
)


def _id() -> str:
    return str(uuid4())


def _iso(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _loads(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


class DatabaseStore:
    async def ensure_schema(self) -> None:
        statements = [
            """
            create table if not exists projects (
              id char(36) primary key,
              name varchar(120) not null,
              description text not null,
              aspect_ratio varchar(20) not null default '16:9',
              status varchar(20) not null default 'active',
              style_prompt text,
              style_reference_image_file_id char(36),
              auto_apply_style_prompt boolean not null default false,
              auto_apply_style_reference boolean not null default false,
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              index idx_projects_created_at (created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists project_scripts (
              id char(36) primary key,
              project_id char(36) not null unique,
              content mediumtext not null,
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_project_scripts_project foreign key (project_id) references projects(id) on delete cascade
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists media_files (
              id char(36) primary key,
              project_id char(36),
              file_type varchar(20) not null,
              bucket varchar(255) not null default '',
              object_key varchar(1024) not null default '',
              url text not null,
              mime_type varchar(120) not null default '',
              width int,
              height int,
              duration_ms int,
              size_bytes bigint,
              metadata json not null,
              status varchar(20) not null default 'pending',
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_media_files_project foreign key (project_id) references projects(id) on delete cascade,
              index idx_media_files_project (project_id, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists assets (
              id char(36) primary key,
              project_id char(36) not null,
              type varchar(20) not null,
              name varchar(120) not null,
              description text not null,
              default_prompt text not null,
              tags json not null,
              image_file_id char(36),
              sort_order int not null default 0,
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_assets_project foreign key (project_id) references projects(id) on delete cascade,
              constraint fk_assets_image_file foreign key (image_file_id) references media_files(id) on delete set null,
              index idx_assets_project_type (project_id, type, sort_order, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists frames (
              id char(36) primary key,
              project_id char(36) not null,
              order_index int not null,
              summary text not null,
              duration_ms int not null default 3000,
              people text not null,
              dialogue text not null,
              action text not null,
              emotion text not null,
              note text not null,
              current_prompt text not null,
              selected_version_id char(36),
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              unique key uq_frames_project_order (project_id, order_index),
              constraint fk_frames_project foreign key (project_id) references projects(id) on delete cascade,
              index idx_frames_project_order (project_id, order_index)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists generation_tasks (
              id char(36) primary key,
              project_id char(36),
              task_type varchar(40) not null,
              provider varchar(80) not null,
              model_name varchar(120) not null,
              status varchar(20) not null default 'queued',
              prompt text not null,
              aspect_ratio varchar(20) not null,
              size varchar(40) not null,
              request_payload json not null,
              images json not null,
              usage_json json,
              response_payload json not null,
              error_message text,
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_generation_tasks_project foreign key (project_id) references projects(id) on delete cascade,
              index idx_generation_tasks_status (status, created_at),
              index idx_generation_tasks_project (project_id, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists frame_versions (
              id char(36) primary key,
              frame_id char(36) not null,
              version_no int not null,
              image_file_id char(36),
              generation_task_id char(36),
              prompt text not null,
              note text not null,
              metadata json not null,
              created_at datetime(6) not null default current_timestamp(6),
              unique key uq_frame_versions_frame_version (frame_id, version_no),
              constraint fk_frame_versions_frame foreign key (frame_id) references frames(id) on delete cascade,
              constraint fk_frame_versions_image_file foreign key (image_file_id) references media_files(id) on delete set null,
              constraint fk_frame_versions_generation_task foreign key (generation_task_id) references generation_tasks(id) on delete set null,
              index idx_frame_versions_frame (frame_id, version_no)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
        ]
        async with engine.begin() as conn:
            for statement in statements:
                await conn.execute(text(statement))
            await self._ensure_column(conn, "projects", "style_prompt", "text")
            await self._ensure_column(conn, "projects", "style_reference_image_file_id", "char(36)")
            await self._ensure_column(conn, "projects", "auto_apply_style_prompt", "boolean not null default false")
            await self._ensure_column(conn, "projects", "auto_apply_style_reference", "boolean not null default false")
            await self._ensure_column_definition(conn, "project_scripts", "content", "mediumtext not null")

    async def _ensure_column(self, conn, table: str, column: str, definition: str) -> None:
        exists = await conn.scalar(
            text(
                "select count(*) from information_schema.columns "
                "where table_schema = database() and table_name = :table and column_name = :column"
            ),
            {"table": table, "column": column},
        )
        if not exists:
            await conn.execute(text(f"alter table {table} add column {column} {definition}"))

    async def _ensure_column_definition(self, conn, table: str, column: str, definition: str) -> None:
        exists = await conn.scalar(
            text(
                "select count(*) from information_schema.columns "
                "where table_schema = database() and table_name = :table and column_name = :column"
            ),
            {"table": table, "column": column},
        )
        if exists:
            await conn.execute(text(f"alter table {table} modify column {column} {definition}"))

    def reset(self) -> None:
        asyncio.run(self.reset_async())

    async def reset_async(self) -> None:
        self._assert_reset_is_safe()
        await self.ensure_schema()
        async with engine.begin() as conn:
            await conn.execute(text("set foreign_key_checks=0"))
            for table in (
                "frame_versions",
                "generation_tasks",
                "assets",
                "frames",
                "media_files",
                "project_scripts",
                "projects",
            ):
                await conn.execute(text(f"delete from {table}"))
            await conn.execute(text("set foreign_key_checks=1"))

    def _assert_reset_is_safe(self) -> None:
        if settings.app_env != "test":
            raise RuntimeError(
                f"Refusing to reset database while APP_ENV={settings.app_env!r}. "
                "Database cleanup is only allowed in APP_ENV='test'."
            )
        database_name = urlparse(settings.database_url).path.lstrip("/")
        database_name = database_name.split("?", 1)[0]
        if not database_name.endswith("_test"):
            raise RuntimeError(
                f"Refusing to reset non-test database '{database_name}'. "
                "Use a *_test database for test cleanup."
            )

    async def create_project(self, name: str, description: str = "", aspect_ratio: str = "16:9") -> ProjectRecord:
        project_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into projects (id, name, description, aspect_ratio, status, style_prompt, auto_apply_style_prompt, auto_apply_style_reference) "
                    "values (:id, :name, :description, :aspect_ratio, 'active', '', false, false)"
                ),
                {"id": project_id, "name": name, "description": description, "aspect_ratio": aspect_ratio},
            )
            await conn.execute(
                text("insert into project_scripts (id, project_id, content) values (:id, :project_id, '')"),
                {"id": _id(), "project_id": project_id},
            )
            await conn.execute(
                text(
                    "insert into frames (id, project_id, order_index, summary, duration_ms, people, dialogue, action, emotion, note, current_prompt) "
                    "values (:id, :project_id, 1, '首个关键帧', 3000, '', '', '', '', '', '')"
                ),
                {"id": _id(), "project_id": project_id},
            )
        project = await self.get_project(project_id)
        assert project
        return project

    async def list_projects(self) -> list[ProjectRecord]:
        async with engine.connect() as conn:
            rows = (await conn.execute(text("select * from projects order by created_at desc"))).mappings().all()
        return [self._project(row) for row in rows]

    async def get_project(self, project_id: str) -> ProjectRecord | None:
        async with engine.connect() as conn:
            row = (await conn.execute(text("select * from projects where id=:id"), {"id": project_id})).mappings().first()
        return self._project(row) if row else None

    async def update_project(self, project_id: str, values: dict[str, object]) -> ProjectRecord | None:
        allowed_fields = {
            "name",
            "description",
            "aspect_ratio",
            "status",
            "style_prompt",
            "style_reference_image_file_id",
            "auto_apply_style_prompt",
            "auto_apply_style_reference",
        }
        nullable_fields = {"style_reference_image_file_id"}
        allowed = {
            k: v
            for k, v in values.items()
            if k in allowed_fields and (v is not None or k in nullable_fields)
        }
        if allowed:
            set_sql = ", ".join(f"{key}=:{key}" for key in allowed)
            async with engine.begin() as conn:
                await conn.execute(text(f"update projects set {set_sql} where id=:id"), {**allowed, "id": project_id})
        return await self.get_project(project_id)

    async def delete_project(self, project_id: str) -> bool:
        async with engine.begin() as conn:
            result = await conn.execute(text("delete from projects where id=:id"), {"id": project_id})
        return result.rowcount > 0

    async def get_script(self, project_id: str) -> ScriptRecord | None:
        async with engine.connect() as conn:
            row = (await conn.execute(text("select * from project_scripts where project_id=:project_id"), {"project_id": project_id})).mappings().first()
        return ScriptRecord(project_id=row["project_id"], content=row["content"], updated_at=_iso(row["updated_at"])) if row else None

    async def update_script(self, project_id: str, content: str) -> ScriptRecord | None:
        if not await self.get_project(project_id):
            return None
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into project_scripts (id, project_id, content) values (:id, :project_id, :content) "
                    "on duplicate key update content=values(content)"
                ),
                {"id": _id(), "project_id": project_id, "content": content},
            )
        return await self.get_script(project_id)

    async def clear_script(self, project_id: str) -> ScriptRecord | None:
        return await self.update_script(project_id, "")

    async def list_frames(self, project_id: str) -> list[FrameRecord]:
        async with engine.connect() as conn:
            rows = (await conn.execute(text("select * from frames where project_id=:project_id order by order_index"), {"project_id": project_id})).mappings().all()
        return [await self._frame_with_versions(row) for row in rows]

    async def create_frame(self, project_id: str, summary: str = "", order_index: int | None = None, duration_ms: int = 3000, current_prompt: str = "") -> FrameRecord | None:
        if not await self.get_project(project_id):
            return None
        if order_index is None:
            order_index = len(await self.list_frames(project_id)) + 1
        frame_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into frames (id, project_id, order_index, summary, duration_ms, people, dialogue, action, emotion, note, current_prompt) "
                    "values (:id, :project_id, :order_index, :summary, :duration_ms, '', '', '', '', '', :current_prompt)"
                ),
                {"id": frame_id, "project_id": project_id, "order_index": order_index, "summary": summary, "duration_ms": duration_ms, "current_prompt": current_prompt},
            )
        return await self.get_frame(frame_id)

    async def get_frame(self, frame_id: str) -> FrameRecord | None:
        async with engine.connect() as conn:
            row = (await conn.execute(text("select * from frames where id=:id"), {"id": frame_id})).mappings().first()
        return await self._frame_with_versions(row) if row else None

    async def update_frame(self, frame_id: str, values: dict[str, object]) -> FrameRecord | None:
        allowed = {k: v for k, v in values.items() if k in {"summary", "duration_ms", "people", "dialogue", "action", "emotion", "note", "current_prompt", "selected_version_id"}}
        if allowed:
            set_sql = ", ".join(f"{key}=:{key}" for key in allowed)
            async with engine.begin() as conn:
                await conn.execute(text(f"update frames set {set_sql} where id=:id"), {**allowed, "id": frame_id})
        return await self.get_frame(frame_id)

    async def delete_frame(self, frame_id: str) -> bool:
        async with engine.begin() as conn:
            result = await conn.execute(text("delete from frames where id=:id"), {"id": frame_id})
        return result.rowcount > 0

    async def list_frame_versions(self, frame_id: str) -> list[FrameVersionRecord]:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "select fv.*, mf.url as image_url from frame_versions fv "
                        "left join media_files mf on mf.id=fv.image_file_id "
                        "where fv.frame_id=:frame_id order by fv.version_no"
                    ),
                    {"frame_id": frame_id},
                )
            ).mappings().all()
        return [self._frame_version(row) for row in rows]

    async def create_frame_version(
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
        frame = await self.get_frame(frame_id)
        if not frame:
            return None
        if image_file_id and not await self.get_media_file(image_file_id):
            return None
        if generation_task_id and not await self.get_generation_task(generation_task_id):
            return None

        async with engine.begin() as conn:
            version_no = (
                await conn.scalar(
                    text("select coalesce(max(version_no), 0) + 1 from frame_versions where frame_id=:frame_id"),
                    {"frame_id": frame_id},
                )
            ) or 1
            version_id = _id()
            await conn.execute(
                text(
                    "insert into frame_versions (id, frame_id, version_no, image_file_id, generation_task_id, prompt, note, metadata) "
                    "values (:id, :frame_id, :version_no, :image_file_id, :generation_task_id, :prompt, :note, :metadata)"
                ),
                {
                    "id": version_id,
                    "frame_id": frame_id,
                    "version_no": version_no,
                    "image_file_id": image_file_id,
                    "generation_task_id": generation_task_id,
                    "prompt": prompt,
                    "note": note,
                    "metadata": _json(metadata or {}),
                },
            )
            if select:
                await conn.execute(
                    text(
                        "update frames set selected_version_id=:version_id, current_prompt=:prompt, "
                        "summary=case when summary='' then :summary else summary end where id=:frame_id"
                    ),
                    {
                        "frame_id": frame_id,
                        "version_id": version_id,
                        "prompt": prompt or frame.current_prompt,
                        "summary": note or prompt,
                    },
                )
        versions = await self.list_frame_versions(frame_id)
        return next((version for version in versions if version.version_no == version_no), None)

    async def select_frame_version(self, frame_id: str, version_id: str) -> FrameRecord | None:
        async with engine.begin() as conn:
            exists = await conn.scalar(
                text("select count(*) from frame_versions where id=:version_id and frame_id=:frame_id"),
                {"frame_id": frame_id, "version_id": version_id},
            )
            if not exists:
                return None
            await conn.execute(
                text("update frames set selected_version_id=:version_id where id=:frame_id"),
                {"frame_id": frame_id, "version_id": version_id},
            )
        return await self.get_frame(frame_id)

    async def list_assets(self, project_id: str) -> list[AssetRecord]:
        async with engine.connect() as conn:
            rows = (await conn.execute(text("select * from assets where project_id=:project_id order by sort_order, created_at"), {"project_id": project_id})).mappings().all()
        return [self._asset(row) for row in rows]

    async def create_asset(self, project_id: str, name: str, type: str = "other", description: str = "", default_prompt: str = "", tags: list[str] | None = None, image_file_id: str | None = None, sort_order: int = 0) -> AssetRecord | None:
        if not await self.get_project(project_id):
            return None
        asset_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into assets (id, project_id, type, name, description, default_prompt, tags, image_file_id, sort_order) "
                    "values (:id, :project_id, :type, :name, :description, :default_prompt, :tags, :image_file_id, :sort_order)"
                ),
                {"id": asset_id, "project_id": project_id, "type": type, "name": name, "description": description, "default_prompt": default_prompt, "tags": _json(tags or []), "image_file_id": image_file_id, "sort_order": sort_order},
            )
        return await self.get_asset(asset_id)

    async def get_asset(self, asset_id: str) -> AssetRecord | None:
        async with engine.connect() as conn:
            row = (await conn.execute(text("select * from assets where id=:id"), {"id": asset_id})).mappings().first()
        return self._asset(row) if row else None

    async def update_asset(self, asset_id: str, values: dict[str, object]) -> AssetRecord | None:
        allowed = {k: v for k, v in values.items() if k in {"name", "type", "description", "default_prompt", "tags", "image_file_id", "sort_order"}}
        if "tags" in allowed:
            allowed["tags"] = _json(allowed["tags"])
        if allowed:
            set_sql = ", ".join(f"{key}=:{key}" for key in allowed)
            async with engine.begin() as conn:
                await conn.execute(text(f"update assets set {set_sql} where id=:id"), {**allowed, "id": asset_id})
        return await self.get_asset(asset_id)

    async def delete_asset(self, asset_id: str) -> bool:
        async with engine.begin() as conn:
            result = await conn.execute(text("delete from assets where id=:id"), {"id": asset_id})
        return result.rowcount > 0

    async def create_media_file(self, *, project_id: str | None, file_type: str, bucket: str, object_key: str, url: str, mime_type: str, size_bytes: int | None = None, metadata: dict[str, Any] | None = None) -> MediaFileRecord | None:
        if project_id and not await self.get_project(project_id):
            return None
        media_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into media_files (id, project_id, file_type, bucket, object_key, url, mime_type, size_bytes, metadata, status) "
                    "values (:id, :project_id, :file_type, :bucket, :object_key, :url, :mime_type, :size_bytes, :metadata, 'pending')"
                ),
                {"id": media_id, "project_id": project_id, "file_type": file_type, "bucket": bucket, "object_key": object_key, "url": url, "mime_type": mime_type, "size_bytes": size_bytes, "metadata": _json(metadata or {})},
            )
        return await self.get_media_file(media_id)

    async def get_media_file(self, media_file_id: str) -> MediaFileRecord | None:
        async with engine.connect() as conn:
            row = (await conn.execute(text("select * from media_files where id=:id"), {"id": media_file_id})).mappings().first()
        return self._media(row) if row else None

    async def complete_media_file(self, media_file_id: str, *, width: int | None = None, height: int | None = None, duration_ms: int | None = None, size_bytes: int | None = None, metadata: dict[str, Any] | None = None) -> MediaFileRecord | None:
        media = await self.get_media_file(media_file_id)
        if not media:
            return None
        merged_metadata = {**media.metadata, **(metadata or {})}
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "update media_files set status='uploaded', width=coalesce(:width, width), height=coalesce(:height, height), "
                    "duration_ms=coalesce(:duration_ms, duration_ms), size_bytes=coalesce(:size_bytes, size_bytes), metadata=:metadata where id=:id"
                ),
                {"id": media_file_id, "width": width, "height": height, "duration_ms": duration_ms, "size_bytes": size_bytes, "metadata": _json(merged_metadata)},
            )
        return await self.get_media_file(media_file_id)

    async def create_generation_task(self, *, provider: str = "volcengine_ark", task_type: str, model_name: str, prompt: str, aspect_ratio: str, size: str, request_payload: dict[str, Any]) -> GenerationTaskRecord:
        task_id = _id()
        project_id = request_payload.get("project_id")
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into generation_tasks (id, project_id, task_type, provider, model_name, status, prompt, aspect_ratio, size, request_payload, images, response_payload) "
                    "values (:id, :project_id, :task_type, :provider, :model_name, 'queued', :prompt, :aspect_ratio, :size, :request_payload, '[]', '{}')"
                ),
                {"id": task_id, "project_id": project_id, "provider": provider, "task_type": task_type, "model_name": model_name, "prompt": prompt, "aspect_ratio": aspect_ratio, "size": size, "request_payload": _json(request_payload)},
            )
        task = await self.get_generation_task(task_id)
        assert task
        return task

    async def get_generation_task(self, task_id: str) -> GenerationTaskRecord | None:
        async with engine.connect() as conn:
            row = (await conn.execute(text("select * from generation_tasks where id=:id"), {"id": task_id})).mappings().first()
        return self._task(row) if row else None

    async def update_generation_task(self, task_id: str, *, status: str | None = None, images: list[dict[str, Any]] | None = None, usage: dict[str, Any] | None = None, response_payload: dict[str, Any] | None = None, error_message: str | None = None) -> GenerationTaskRecord | None:
        values: dict[str, Any] = {}
        if status is not None:
            values["status"] = status
        if images is not None:
            values["images"] = _json(images)
        if usage is not None:
            values["usage_json"] = _json(usage)
        if response_payload is not None:
            values["response_payload"] = _json(response_payload)
        if error_message is not None:
            values["error_message"] = error_message
        if values:
            set_sql = ", ".join(f"{key}=:{key}" for key in values)
            async with engine.begin() as conn:
                await conn.execute(text(f"update generation_tasks set {set_sql} where id=:id"), {**values, "id": task_id})
        return await self.get_generation_task(task_id)

    def _project(self, row: Any) -> ProjectRecord:
        return ProjectRecord(id=row["id"], name=row["name"], description=row["description"], aspect_ratio=row["aspect_ratio"], status=row["status"], style_prompt=row["style_prompt"] or "", style_reference_image_file_id=row["style_reference_image_file_id"], auto_apply_style_prompt=bool(row["auto_apply_style_prompt"]), auto_apply_style_reference=bool(row["auto_apply_style_reference"]), created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _frame(self, row: Any) -> FrameRecord:
        return FrameRecord(id=row["id"], project_id=row["project_id"], order_index=row["order_index"], summary=row["summary"], duration_ms=row["duration_ms"], people=row["people"], dialogue=row["dialogue"], action=row["action"], emotion=row["emotion"], note=row["note"], current_prompt=row["current_prompt"], selected_version_id=row["selected_version_id"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    async def _frame_with_versions(self, row: Any) -> FrameRecord:
        frame = self._frame(row)
        versions = await self.list_frame_versions(frame.id)
        return frame.model_copy(update={"versions": versions})

    def _frame_version(self, row: Any) -> FrameVersionRecord:
        return FrameVersionRecord(id=row["id"], frame_id=row["frame_id"], version_no=row["version_no"], image_file_id=row["image_file_id"], image_url=row["image_url"], generation_task_id=row["generation_task_id"], prompt=row["prompt"], note=row["note"], metadata=_loads(row["metadata"], {}), created_at=_iso(row["created_at"]))

    def _asset(self, row: Any) -> AssetRecord:
        return AssetRecord(id=row["id"], project_id=row["project_id"], type=row["type"], name=row["name"], description=row["description"], default_prompt=row["default_prompt"], tags=_loads(row["tags"], []), image_file_id=row["image_file_id"], sort_order=row["sort_order"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _media(self, row: Any) -> MediaFileRecord:
        return MediaFileRecord(id=row["id"], project_id=row["project_id"], file_type=row["file_type"], bucket=row["bucket"], object_key=row["object_key"], url=row["url"], mime_type=row["mime_type"], width=row["width"], height=row["height"], duration_ms=row["duration_ms"], size_bytes=row["size_bytes"], metadata=_loads(row["metadata"], {}), status=row["status"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _task(self, row: Any) -> GenerationTaskRecord:
        return GenerationTaskRecord(id=row["id"], status=row["status"], task_type=row["task_type"], provider=row["provider"], model_name=row["model_name"], prompt=row["prompt"], aspect_ratio=row["aspect_ratio"], size=row["size"], request_payload=_loads(row["request_payload"], {}), images=_loads(row["images"], []), usage=_loads(row["usage_json"], None), response_payload=_loads(row["response_payload"], {}), error_message=row["error_message"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))


store = DatabaseStore()
