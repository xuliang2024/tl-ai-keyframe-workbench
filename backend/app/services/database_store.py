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
    PublicAssetImageRecord,
    PublicAssetRecord,
    ScriptRecord,
    UserMcpTokenRecord,
    UserRecord,
    UserSessionRecord,
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
            create table if not exists users (
              id char(36) primary key,
              email varchar(255) not null,
              username varchar(80) not null,
              password_hash varchar(255) not null,
              display_name varchar(120) not null default '',
              avatar_url text,
              status varchar(20) not null default 'active',
              last_login_at datetime(6),
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              unique key uq_users_email (email),
              unique key uq_users_username (username),
              index idx_users_created_at (created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists user_sessions (
              id char(36) primary key,
              user_id char(36) not null,
              refresh_token_hash char(64) not null,
              expires_at datetime(6) not null,
              revoked_at datetime(6),
              created_at datetime(6) not null default current_timestamp(6),
              unique key uq_user_sessions_refresh_token_hash (refresh_token_hash),
              constraint fk_user_sessions_user foreign key (user_id) references users(id) on delete cascade,
              index idx_user_sessions_user (user_id, created_at desc),
              index idx_user_sessions_token (refresh_token_hash, expires_at)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists user_mcp_tokens (
              id char(36) primary key,
              user_id char(36) not null,
              name varchar(120) not null,
              token_hash char(64) not null,
              last_used_at datetime(6),
              revoked_at datetime(6),
              created_at datetime(6) not null default current_timestamp(6),
              unique key uq_user_mcp_tokens_token_hash (token_hash),
              constraint fk_user_mcp_tokens_user foreign key (user_id) references users(id) on delete cascade,
              index idx_user_mcp_tokens_user (user_id, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists projects (
              id char(36) primary key,
              owner_user_id char(36),
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
              constraint fk_projects_owner_user foreign key (owner_user_id) references users(id) on delete set null,
              index idx_projects_owner_created_at (owner_user_id, created_at desc),
              index idx_projects_created_at (created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists project_scripts (
              id char(36) primary key,
              project_id char(36) not null unique,
              owner_user_id char(36),
              content mediumtext not null,
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_project_scripts_owner_user foreign key (owner_user_id) references users(id) on delete set null,
              constraint fk_project_scripts_project foreign key (project_id) references projects(id) on delete cascade
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists media_files (
              id char(36) primary key,
              project_id char(36),
              owner_user_id char(36),
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
              constraint fk_media_files_owner_user foreign key (owner_user_id) references users(id) on delete set null,
              constraint fk_media_files_project foreign key (project_id) references projects(id) on delete cascade,
              index idx_media_files_owner (owner_user_id, created_at desc),
              index idx_media_files_project (project_id, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists assets (
              id char(36) primary key,
              project_id char(36) not null,
              owner_user_id char(36),
              type varchar(20) not null,
              name varchar(120) not null,
              description text not null,
              default_prompt text not null,
              tags json not null,
              image_file_id char(36),
              sort_order int not null default 0,
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_assets_owner_user foreign key (owner_user_id) references users(id) on delete set null,
              constraint fk_assets_project foreign key (project_id) references projects(id) on delete cascade,
              constraint fk_assets_image_file foreign key (image_file_id) references media_files(id) on delete set null,
              index idx_assets_owner (owner_user_id, created_at desc),
              index idx_assets_project_type (project_id, type, sort_order, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists public_assets (
              id char(36) primary key,
              type varchar(20) not null,
              name varchar(120) not null,
              description text not null,
              default_prompt text not null,
              tags json not null,
              image_file_id char(36),
              sort_order int not null default 0,
              status varchar(20) not null default 'active',
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_public_assets_image_file foreign key (image_file_id) references media_files(id) on delete set null,
              index idx_public_assets_type (type, sort_order, created_at desc),
              index idx_public_assets_status (status, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists public_asset_images (
              id char(36) primary key,
              public_asset_id char(36) not null,
              media_file_id char(36) not null,
              role varchar(40) not null default 'reference',
              title varchar(120) not null default '',
              description text not null,
              prompt text not null,
              scene_prompt text not null,
              angle varchar(40) not null default '',
              tags json not null,
              is_primary boolean not null default false,
              sort_order int not null default 0,
              created_at datetime(6) not null default current_timestamp(6),
              updated_at datetime(6) not null default current_timestamp(6) on update current_timestamp(6),
              constraint fk_public_asset_images_asset foreign key (public_asset_id) references public_assets(id) on delete cascade,
              constraint fk_public_asset_images_media foreign key (media_file_id) references media_files(id) on delete cascade,
              index idx_public_asset_images_asset (public_asset_id, sort_order, created_at),
              index idx_public_asset_images_role (public_asset_id, role, sort_order)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists frames (
              id char(36) primary key,
              project_id char(36) not null,
              owner_user_id char(36),
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
              constraint fk_frames_owner_user foreign key (owner_user_id) references users(id) on delete set null,
              constraint fk_frames_project foreign key (project_id) references projects(id) on delete cascade,
              index idx_frames_owner (owner_user_id, created_at desc),
              index idx_frames_project_order (project_id, order_index)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists generation_tasks (
              id char(36) primary key,
              owner_user_id char(36),
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
              constraint fk_generation_tasks_owner_user foreign key (owner_user_id) references users(id) on delete set null,
              constraint fk_generation_tasks_project foreign key (project_id) references projects(id) on delete cascade,
              index idx_generation_tasks_owner (owner_user_id, created_at desc),
              index idx_generation_tasks_status (status, created_at),
              index idx_generation_tasks_project (project_id, created_at desc)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """,
            """
            create table if not exists frame_versions (
              id char(36) primary key,
              frame_id char(36) not null,
              owner_user_id char(36),
              version_no int not null,
              image_file_id char(36),
              generation_task_id char(36),
              prompt text not null,
              note text not null,
              metadata json not null,
              created_at datetime(6) not null default current_timestamp(6),
              unique key uq_frame_versions_frame_version (frame_id, version_no),
              constraint fk_frame_versions_owner_user foreign key (owner_user_id) references users(id) on delete set null,
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
            for table in (
                "projects",
                "project_scripts",
                "media_files",
                "assets",
                "frames",
                "generation_tasks",
                "frame_versions",
            ):
                await self._ensure_column(conn, table, "owner_user_id", "char(36)")
            await self._ensure_column(conn, "projects", "style_prompt", "text")
            await self._ensure_column(conn, "projects", "style_reference_image_file_id", "char(36)")
            await self._ensure_column(conn, "projects", "auto_apply_style_prompt", "boolean not null default false")
            await self._ensure_column(conn, "projects", "auto_apply_style_reference", "boolean not null default false")
            await self._ensure_column_definition(conn, "project_scripts", "content", "mediumtext not null")
            await self._ensure_column(conn, "generation_tasks", "target_type", "varchar(80)")
            await self._ensure_column(conn, "generation_tasks", "target_id", "char(36)")
            await self._ensure_column(conn, "generation_tasks", "target_payload", "json")
            await self._ensure_column(conn, "generation_tasks", "reference_payload", "json")
            await self._ensure_column(conn, "public_asset_images", "source_type", "varchar(32) not null default 'uploaded'")
            await self._ensure_column(conn, "public_asset_images", "generation_task_id", "char(36)")
            await self._ensure_column(conn, "public_asset_images", "generation_prompt", "text")
            await self._ensure_column(conn, "public_asset_images", "created_by_user_id", "char(36)")

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
                "user_mcp_tokens",
                "user_sessions",
                "frame_versions",
                "generation_tasks",
                "assets",
                "public_asset_images",
                "public_assets",
                "frames",
                "media_files",
                "project_scripts",
                "projects",
                "users",
            ):
                await conn.execute(text(f"delete from {table}"))
            await conn.execute(text("set foreign_key_checks=1"))

    async def create_user(
        self,
        *,
        email: str,
        username: str,
        password_hash: str,
        display_name: str = "",
    ) -> UserRecord:
        user_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into users (id, email, username, password_hash, display_name, status) "
                    "values (:id, :email, :username, :password_hash, :display_name, 'active')"
                ),
                {
                    "id": user_id,
                    "email": email,
                    "username": username,
                    "password_hash": password_hash,
                    "display_name": display_name,
                },
            )
        user = await self.get_user(user_id)
        assert user
        return user

    async def get_user(self, user_id: str) -> UserRecord | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(text("select * from users where id=:id"), {"id": user_id})
            ).mappings().first()
        return self._user(row) if row else None

    async def get_user_by_email(self, email: str) -> UserRecord | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(text("select * from users where email=:email"), {"email": email})
            ).mappings().first()
        return self._user(row) if row else None

    async def get_user_by_username(self, username: str) -> UserRecord | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("select * from users where username=:username"),
                    {"username": username},
                )
            ).mappings().first()
        return self._user(row) if row else None

    async def get_user_by_login(self, login: str) -> UserRecord | None:
        normalized = login.lower()
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("select * from users where email=:login or username=:login"),
                    {"login": normalized},
                )
            ).mappings().first()
        return self._user(row) if row else None

    async def touch_user_login(self, user_id: str) -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text("update users set last_login_at=current_timestamp(6) where id=:id"),
                {"id": user_id},
            )

    async def create_user_session(
        self,
        *,
        user_id: str,
        refresh_token_hash: str,
        expires_at,
    ) -> UserSessionRecord:
        session_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into user_sessions (id, user_id, refresh_token_hash, expires_at) "
                    "values (:id, :user_id, :refresh_token_hash, :expires_at)"
                ),
                {
                    "id": session_id,
                    "user_id": user_id,
                    "refresh_token_hash": refresh_token_hash,
                    "expires_at": expires_at,
                },
            )
        session = await self.get_user_session_by_hash(refresh_token_hash)
        assert session
        return session

    async def get_user_session_by_hash(self, refresh_token_hash: str) -> UserSessionRecord | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "select * from user_sessions "
                        "where refresh_token_hash=:refresh_token_hash "
                        "and revoked_at is null and expires_at > current_timestamp(6)"
                    ),
                    {"refresh_token_hash": refresh_token_hash},
                )
            ).mappings().first()
        return self._user_session(row) if row else None

    async def revoke_user_session(self, session_id: str) -> bool:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "update user_sessions set revoked_at=current_timestamp(6) "
                    "where id=:id and revoked_at is null"
                ),
                {"id": session_id},
            )
        return result.rowcount > 0

    async def create_user_mcp_token(
        self,
        *,
        user_id: str,
        name: str,
        token_hash: str,
    ) -> UserMcpTokenRecord:
        token_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into user_mcp_tokens (id, user_id, name, token_hash) "
                    "values (:id, :user_id, :name, :token_hash)"
                ),
                {
                    "id": token_id,
                    "user_id": user_id,
                    "name": name,
                    "token_hash": token_hash,
                },
            )
        token = await self.get_user_mcp_token(token_id, user_id=user_id)
        assert token
        return token

    async def list_user_mcp_tokens(self, user_id: str) -> list[UserMcpTokenRecord]:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "select * from user_mcp_tokens "
                        "where user_id=:user_id and revoked_at is null "
                        "order by created_at desc"
                    ),
                    {"user_id": user_id},
                )
            ).mappings().all()
        return [self._user_mcp_token(row) for row in rows]

    async def get_user_mcp_token(
        self,
        token_id: str,
        *,
        user_id: str | None = None,
    ) -> UserMcpTokenRecord | None:
        where_sql = "id=:id"
        params = {"id": token_id}
        if user_id:
            where_sql += " and user_id=:user_id"
            params["user_id"] = user_id
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(f"select * from user_mcp_tokens where {where_sql}"),
                    params,
                )
            ).mappings().first()
        return self._user_mcp_token(row) if row else None

    async def get_user_mcp_token_by_hash(self, token_hash: str) -> UserMcpTokenRecord | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "select * from user_mcp_tokens "
                        "where token_hash=:token_hash and revoked_at is null"
                    ),
                    {"token_hash": token_hash},
                )
            ).mappings().first()
        return self._user_mcp_token(row) if row else None

    async def touch_user_mcp_token(self, token_id: str) -> None:
        async with engine.begin() as conn:
            await conn.execute(
                text("update user_mcp_tokens set last_used_at=current_timestamp(6) where id=:id"),
                {"id": token_id},
            )

    async def revoke_user_mcp_token(self, token_id: str, *, user_id: str) -> bool:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "update user_mcp_tokens set revoked_at=current_timestamp(6) "
                    "where id=:id and user_id=:user_id and revoked_at is null"
                ),
                {"id": token_id, "user_id": user_id},
            )
        return result.rowcount > 0

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

    async def create_project(
        self,
        name: str,
        description: str = "",
        aspect_ratio: str = "16:9",
        owner_user_id: str | None = None,
    ) -> ProjectRecord:
        project_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into projects (id, owner_user_id, name, description, aspect_ratio, status, style_prompt, auto_apply_style_prompt, auto_apply_style_reference) "
                    "values (:id, :owner_user_id, :name, :description, :aspect_ratio, 'active', '', false, false)"
                ),
                {
                    "id": project_id,
                    "owner_user_id": owner_user_id,
                    "name": name,
                    "description": description,
                    "aspect_ratio": aspect_ratio,
                },
            )
            await conn.execute(
                text(
                    "insert into project_scripts (id, project_id, owner_user_id, content) "
                    "values (:id, :project_id, :owner_user_id, '')"
                ),
                {"id": _id(), "project_id": project_id, "owner_user_id": owner_user_id},
            )
            await conn.execute(
                text(
                    "insert into frames (id, project_id, owner_user_id, order_index, summary, duration_ms, people, dialogue, action, emotion, note, current_prompt) "
                    "values (:id, :project_id, :owner_user_id, 1, '首个关键帧', 3000, '', '', '', '', '', '')"
                ),
                {"id": _id(), "project_id": project_id, "owner_user_id": owner_user_id},
            )
        project = await self.get_project(project_id, owner_user_id=owner_user_id)
        assert project
        return project

    async def list_projects(self, owner_user_id: str | None = None) -> list[ProjectRecord]:
        async with engine.connect() as conn:
            if owner_user_id:
                rows = (
                    await conn.execute(
                        text(
                            "select * from projects where owner_user_id=:owner_user_id "
                            "order by created_at desc"
                        ),
                        {"owner_user_id": owner_user_id},
                    )
                ).mappings().all()
            else:
                rows = (
                    await conn.execute(text("select * from projects order by created_at desc"))
                ).mappings().all()
        return [self._project(row) for row in rows]

    async def get_project(
        self,
        project_id: str,
        owner_user_id: str | None = None,
    ) -> ProjectRecord | None:
        async with engine.connect() as conn:
            if owner_user_id:
                row = (
                    await conn.execute(
                        text("select * from projects where id=:id and owner_user_id=:owner_user_id"),
                        {"id": project_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().first()
            else:
                row = (
                    await conn.execute(text("select * from projects where id=:id"), {"id": project_id})
                ).mappings().first()
        return self._project(row) if row else None

    async def update_project(
        self,
        project_id: str,
        values: dict[str, object],
        owner_user_id: str | None = None,
    ) -> ProjectRecord | None:
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
            where_sql = "id=:id"
            params = {**allowed, "id": project_id}
            if owner_user_id:
                where_sql += " and owner_user_id=:owner_user_id"
                params["owner_user_id"] = owner_user_id
            async with engine.begin() as conn:
                await conn.execute(text(f"update projects set {set_sql} where {where_sql}"), params)
        return await self.get_project(project_id, owner_user_id=owner_user_id)

    async def delete_project(self, project_id: str, owner_user_id: str | None = None) -> bool:
        where_sql = "id=:id"
        params = {"id": project_id}
        if owner_user_id:
            where_sql += " and owner_user_id=:owner_user_id"
            params["owner_user_id"] = owner_user_id
        async with engine.begin() as conn:
            result = await conn.execute(text(f"delete from projects where {where_sql}"), params)
        return result.rowcount > 0

    async def get_script(self, project_id: str, owner_user_id: str | None = None) -> ScriptRecord | None:
        async with engine.connect() as conn:
            if owner_user_id:
                row = (
                    await conn.execute(
                        text(
                            "select * from project_scripts "
                            "where project_id=:project_id and owner_user_id=:owner_user_id"
                        ),
                        {"project_id": project_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().first()
            else:
                row = (
                    await conn.execute(
                        text("select * from project_scripts where project_id=:project_id"),
                        {"project_id": project_id},
                    )
                ).mappings().first()
        return self._script(row) if row else None

    async def update_script(
        self,
        project_id: str,
        content: str,
        owner_user_id: str | None = None,
    ) -> ScriptRecord | None:
        project = await self.get_project(project_id, owner_user_id=owner_user_id)
        if not project:
            return None
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into project_scripts (id, project_id, owner_user_id, content) "
                    "values (:id, :project_id, :owner_user_id, :content) "
                    "on duplicate key update content=values(content), owner_user_id=values(owner_user_id)"
                ),
                {
                    "id": _id(),
                    "project_id": project_id,
                    "owner_user_id": project.owner_user_id,
                    "content": content,
                },
            )
        return await self.get_script(project_id, owner_user_id=owner_user_id)

    async def clear_script(self, project_id: str, owner_user_id: str | None = None) -> ScriptRecord | None:
        return await self.update_script(project_id, "", owner_user_id=owner_user_id)

    async def list_frames(self, project_id: str, owner_user_id: str | None = None) -> list[FrameRecord]:
        async with engine.connect() as conn:
            if owner_user_id:
                rows = (
                    await conn.execute(
                        text(
                            "select * from frames where project_id=:project_id "
                            "and owner_user_id=:owner_user_id order by order_index"
                        ),
                        {"project_id": project_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().all()
            else:
                rows = (
                    await conn.execute(
                        text("select * from frames where project_id=:project_id order by order_index"),
                        {"project_id": project_id},
                    )
                ).mappings().all()
        return [await self._frame_with_versions(row, owner_user_id=owner_user_id) for row in rows]

    async def create_frame(
        self,
        project_id: str,
        summary: str = "",
        order_index: int | None = None,
        duration_ms: int = 3000,
        current_prompt: str = "",
        owner_user_id: str | None = None,
    ) -> FrameRecord | None:
        project = await self.get_project(project_id, owner_user_id=owner_user_id)
        if not project:
            return None
        if order_index is None:
            order_index = len(await self.list_frames(project_id, owner_user_id=owner_user_id)) + 1
        frame_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into frames (id, project_id, owner_user_id, order_index, summary, duration_ms, people, dialogue, action, emotion, note, current_prompt) "
                    "values (:id, :project_id, :owner_user_id, :order_index, :summary, :duration_ms, '', '', '', '', '', :current_prompt)"
                ),
                {
                    "id": frame_id,
                    "project_id": project_id,
                    "owner_user_id": project.owner_user_id,
                    "order_index": order_index,
                    "summary": summary,
                    "duration_ms": duration_ms,
                    "current_prompt": current_prompt,
                },
            )
        return await self.get_frame(frame_id, owner_user_id=owner_user_id)

    async def get_frame(self, frame_id: str, owner_user_id: str | None = None) -> FrameRecord | None:
        async with engine.connect() as conn:
            if owner_user_id:
                row = (
                    await conn.execute(
                        text("select * from frames where id=:id and owner_user_id=:owner_user_id"),
                        {"id": frame_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().first()
            else:
                row = (
                    await conn.execute(text("select * from frames where id=:id"), {"id": frame_id})
                ).mappings().first()
        return await self._frame_with_versions(row, owner_user_id=owner_user_id) if row else None

    async def update_frame(
        self,
        frame_id: str,
        values: dict[str, object],
        owner_user_id: str | None = None,
    ) -> FrameRecord | None:
        allowed = {k: v for k, v in values.items() if k in {"summary", "duration_ms", "people", "dialogue", "action", "emotion", "note", "current_prompt", "selected_version_id"}}
        if allowed:
            set_sql = ", ".join(f"{key}=:{key}" for key in allowed)
            where_sql = "id=:id"
            params = {**allowed, "id": frame_id}
            if owner_user_id:
                where_sql += " and owner_user_id=:owner_user_id"
                params["owner_user_id"] = owner_user_id
            async with engine.begin() as conn:
                await conn.execute(text(f"update frames set {set_sql} where {where_sql}"), params)
        return await self.get_frame(frame_id, owner_user_id=owner_user_id)

    async def delete_frame(self, frame_id: str, owner_user_id: str | None = None) -> bool:
        where_sql = "id=:id"
        params = {"id": frame_id}
        if owner_user_id:
            where_sql += " and owner_user_id=:owner_user_id"
            params["owner_user_id"] = owner_user_id
        async with engine.begin() as conn:
            result = await conn.execute(text(f"delete from frames where {where_sql}"), params)
        return result.rowcount > 0

    async def list_frame_versions(
        self,
        frame_id: str,
        owner_user_id: str | None = None,
    ) -> list[FrameVersionRecord]:
        async with engine.connect() as conn:
            owner_sql = " and fv.owner_user_id=:owner_user_id" if owner_user_id else ""
            params = {"frame_id": frame_id}
            if owner_user_id:
                params["owner_user_id"] = owner_user_id
            rows = (
                await conn.execute(
                    text(
                        "select fv.*, mf.url as image_url from frame_versions fv "
                        "left join media_files mf on mf.id=fv.image_file_id "
                        f"where fv.frame_id=:frame_id{owner_sql} order by fv.version_no"
                    ),
                    params,
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
        owner_user_id: str | None = None,
    ) -> FrameVersionRecord | None:
        frame = await self.get_frame(frame_id, owner_user_id=owner_user_id)
        if not frame:
            return None
        if image_file_id and not await self.get_media_file(image_file_id, owner_user_id=owner_user_id):
            return None
        if generation_task_id and not await self.get_generation_task(generation_task_id, owner_user_id=owner_user_id):
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
                    "insert into frame_versions (id, frame_id, owner_user_id, version_no, image_file_id, generation_task_id, prompt, note, metadata) "
                    "values (:id, :frame_id, :owner_user_id, :version_no, :image_file_id, :generation_task_id, :prompt, :note, :metadata)"
                ),
                {
                    "id": version_id,
                    "frame_id": frame_id,
                    "owner_user_id": frame.owner_user_id,
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
        versions = await self.list_frame_versions(frame_id, owner_user_id=owner_user_id)
        return next((version for version in versions if version.version_no == version_no), None)

    async def select_frame_version(
        self,
        frame_id: str,
        version_id: str,
        owner_user_id: str | None = None,
    ) -> FrameRecord | None:
        async with engine.begin() as conn:
            owner_sql = " and owner_user_id=:owner_user_id" if owner_user_id else ""
            params = {"frame_id": frame_id, "version_id": version_id}
            if owner_user_id:
                params["owner_user_id"] = owner_user_id
            exists = await conn.scalar(
                text(
                    "select count(*) from frame_versions "
                    f"where id=:version_id and frame_id=:frame_id{owner_sql}"
                ),
                params,
            )
            if not exists:
                return None
            update_where_sql = "id=:frame_id"
            if owner_user_id:
                update_where_sql += " and owner_user_id=:owner_user_id"
            await conn.execute(
                text(f"update frames set selected_version_id=:version_id where {update_where_sql}"),
                params,
            )
        return await self.get_frame(frame_id, owner_user_id=owner_user_id)

    async def list_assets(self, project_id: str, owner_user_id: str | None = None) -> list[AssetRecord]:
        async with engine.connect() as conn:
            if owner_user_id:
                rows = (
                    await conn.execute(
                        text(
                            "select * from assets where project_id=:project_id "
                            "and owner_user_id=:owner_user_id order by sort_order, created_at"
                        ),
                        {"project_id": project_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().all()
            else:
                rows = (
                    await conn.execute(
                        text("select * from assets where project_id=:project_id order by sort_order, created_at"),
                        {"project_id": project_id},
                    )
                ).mappings().all()
        return [self._asset(row) for row in rows]

    async def create_asset(self, project_id: str, name: str, type: str = "other", description: str = "", default_prompt: str = "", tags: list[str] | None = None, image_file_id: str | None = None, sort_order: int = 0, owner_user_id: str | None = None) -> AssetRecord | None:
        project = await self.get_project(project_id, owner_user_id=owner_user_id)
        if not project:
            return None
        if image_file_id and not await self.get_media_file(image_file_id, owner_user_id=owner_user_id):
            return None
        asset_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into assets (id, project_id, owner_user_id, type, name, description, default_prompt, tags, image_file_id, sort_order) "
                    "values (:id, :project_id, :owner_user_id, :type, :name, :description, :default_prompt, :tags, :image_file_id, :sort_order)"
                ),
                {"id": asset_id, "project_id": project_id, "owner_user_id": project.owner_user_id, "type": type, "name": name, "description": description, "default_prompt": default_prompt, "tags": _json(tags or []), "image_file_id": image_file_id, "sort_order": sort_order},
            )
        return await self.get_asset(asset_id, owner_user_id=owner_user_id)

    async def get_asset(self, asset_id: str, owner_user_id: str | None = None) -> AssetRecord | None:
        async with engine.connect() as conn:
            if owner_user_id:
                row = (
                    await conn.execute(
                        text("select * from assets where id=:id and owner_user_id=:owner_user_id"),
                        {"id": asset_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().first()
            else:
                row = (
                    await conn.execute(text("select * from assets where id=:id"), {"id": asset_id})
                ).mappings().first()
        return self._asset(row) if row else None

    async def update_asset(
        self,
        asset_id: str,
        values: dict[str, object],
        owner_user_id: str | None = None,
    ) -> AssetRecord | None:
        allowed = {k: v for k, v in values.items() if k in {"name", "type", "description", "default_prompt", "tags", "image_file_id", "sort_order"}}
        if "image_file_id" in allowed and allowed["image_file_id"]:
            media = await self.get_media_file(str(allowed["image_file_id"]), owner_user_id=owner_user_id)
            if not media:
                return None
        if "tags" in allowed:
            allowed["tags"] = _json(allowed["tags"])
        if allowed:
            set_sql = ", ".join(f"{key}=:{key}" for key in allowed)
            where_sql = "id=:id"
            params = {**allowed, "id": asset_id}
            if owner_user_id:
                where_sql += " and owner_user_id=:owner_user_id"
                params["owner_user_id"] = owner_user_id
            async with engine.begin() as conn:
                await conn.execute(text(f"update assets set {set_sql} where {where_sql}"), params)
        return await self.get_asset(asset_id, owner_user_id=owner_user_id)

    async def delete_asset(self, asset_id: str, owner_user_id: str | None = None) -> bool:
        where_sql = "id=:id"
        params = {"id": asset_id}
        if owner_user_id:
            where_sql += " and owner_user_id=:owner_user_id"
            params["owner_user_id"] = owner_user_id
        async with engine.begin() as conn:
            result = await conn.execute(text(f"delete from assets where {where_sql}"), params)
        return result.rowcount > 0

    async def list_public_assets(
        self,
        *,
        type: str | None = None,
        keyword: str | None = None,
    ) -> list[PublicAssetRecord]:
        where = ["status='active'"]
        params: dict[str, Any] = {}
        if type and type != "全部":
            where.append("type=:type")
            params["type"] = type
        if keyword:
            where.append("(name like :keyword or description like :keyword or default_prompt like :keyword)")
            params["keyword"] = f"%{keyword}%"
        where_sql = " and ".join(where)
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(f"select * from public_assets where {where_sql} order by sort_order, created_at desc"),
                    params,
                )
            ).mappings().all()
        return [self._public_asset(row) for row in rows]

    async def create_public_asset(
        self,
        *,
        name: str,
        type: str = "other",
        description: str = "",
        default_prompt: str = "",
        tags: list[str] | None = None,
        image_file_id: str | None = None,
        sort_order: int = 0,
        status: str = "active",
    ) -> PublicAssetRecord | None:
        if image_file_id and not await self.get_media_file(image_file_id):
            return None
        public_asset_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into public_assets (id, type, name, description, default_prompt, tags, image_file_id, sort_order, status) "
                    "values (:id, :type, :name, :description, :default_prompt, :tags, :image_file_id, :sort_order, :status)"
                ),
                {
                    "id": public_asset_id,
                    "type": type,
                    "name": name,
                    "description": description,
                    "default_prompt": default_prompt,
                    "tags": _json(tags or []),
                    "image_file_id": image_file_id,
                    "sort_order": sort_order,
                    "status": status,
                },
            )
        return await self.get_public_asset(public_asset_id)

    async def get_public_asset(self, public_asset_id: str) -> PublicAssetRecord | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text("select * from public_assets where id=:id and status='active'"),
                    {"id": public_asset_id},
                )
            ).mappings().first()
        return self._public_asset(row) if row else None

    async def list_public_asset_images(self, public_asset_id: str) -> list[PublicAssetImageRecord]:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        "select pai.*, mf.url as image_url, coalesce(nullif(u.display_name, ''), u.username, u.email) as created_by_name from public_asset_images pai "
                        "join media_files mf on mf.id=pai.media_file_id "
                        "left join users u on u.id=pai.created_by_user_id "
                        "where pai.public_asset_id=:public_asset_id "
                        "order by pai.is_primary desc, pai.sort_order, pai.created_at"
                    ),
                    {"public_asset_id": public_asset_id},
                )
            ).mappings().all()
        return [self._public_asset_image(row) for row in rows]

    async def create_public_asset_image(
        self,
        *,
        public_asset_id: str,
        media_file_id: str,
        role: str = "reference",
        title: str = "",
        description: str = "",
        prompt: str = "",
        scene_prompt: str = "",
        angle: str = "",
        tags: list[str] | None = None,
        is_primary: bool = False,
        sort_order: int = 0,
        source_type: str = "uploaded",
        generation_task_id: str | None = None,
        generation_prompt: str = "",
        created_by_user_id: str | None = None,
    ) -> PublicAssetImageRecord | None:
        public_asset = await self.get_public_asset(public_asset_id)
        media_file = await self.get_media_file(media_file_id)
        if not public_asset or not media_file:
            return None
        image_id = _id()
        async with engine.begin() as conn:
            if is_primary:
                await conn.execute(
                    text("update public_asset_images set is_primary=false where public_asset_id=:public_asset_id"),
                    {"public_asset_id": public_asset_id},
                )
                await conn.execute(
                    text("update public_assets set image_file_id=:media_file_id where id=:public_asset_id"),
                    {"public_asset_id": public_asset_id, "media_file_id": media_file_id},
                )
            await conn.execute(
                text(
                    "insert into public_asset_images (id, public_asset_id, media_file_id, role, title, description, prompt, scene_prompt, angle, tags, is_primary, sort_order, source_type, generation_task_id, generation_prompt, created_by_user_id) "
                    "values (:id, :public_asset_id, :media_file_id, :role, :title, :description, :prompt, :scene_prompt, :angle, :tags, :is_primary, :sort_order, :source_type, :generation_task_id, :generation_prompt, :created_by_user_id)"
                ),
                {
                    "id": image_id,
                    "public_asset_id": public_asset_id,
                    "media_file_id": media_file_id,
                    "role": role,
                    "title": title,
                    "description": description,
                    "prompt": prompt,
                    "scene_prompt": scene_prompt,
                    "angle": angle,
                    "tags": _json(tags or []),
                    "is_primary": is_primary,
                    "sort_order": sort_order,
                    "source_type": source_type,
                    "generation_task_id": generation_task_id,
                    "generation_prompt": generation_prompt,
                    "created_by_user_id": created_by_user_id,
                },
            )
        return await self.get_public_asset_image(image_id)

    async def get_public_asset_image(self, image_id: str) -> PublicAssetImageRecord | None:
        async with engine.connect() as conn:
            row = (
                await conn.execute(
                    text(
                        "select pai.*, mf.url as image_url, coalesce(nullif(u.display_name, ''), u.username, u.email) as created_by_name from public_asset_images pai "
                        "join media_files mf on mf.id=pai.media_file_id "
                        "left join users u on u.id=pai.created_by_user_id "
                        "where pai.id=:id"
                    ),
                    {"id": image_id},
                )
            ).mappings().first()
        return self._public_asset_image(row) if row else None

    async def delete_public_asset_image(self, image_id: str) -> bool:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("delete from public_asset_images where id=:id"),
                {"id": image_id},
            )
        return result.rowcount > 0

    async def copy_media_file_record_to_project(
        self,
        *,
        source_media_file_id: str,
        project_id: str,
        owner_user_id: str,
        object_key: str,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> MediaFileRecord | None:
        project = await self.get_project(project_id, owner_user_id=owner_user_id)
        source = await self.get_media_file(source_media_file_id)
        if not project or not source:
            return None
        media_id = _id()
        merged_metadata = {
            **source.metadata,
            **(metadata or {}),
            "copied_from_media_file_id": source.id,
        }
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into media_files (id, project_id, owner_user_id, file_type, bucket, object_key, url, mime_type, width, height, duration_ms, size_bytes, metadata, status) "
                    "values (:id, :project_id, :owner_user_id, :file_type, :bucket, :object_key, :url, :mime_type, :width, :height, :duration_ms, :size_bytes, :metadata, :status)"
                ),
                {
                    "id": media_id,
                    "project_id": project_id,
                    "owner_user_id": project.owner_user_id,
                    "file_type": source.file_type,
                    "bucket": source.bucket,
                    "object_key": object_key,
                    "url": url,
                    "mime_type": source.mime_type,
                    "width": source.width,
                    "height": source.height,
                    "duration_ms": source.duration_ms,
                    "size_bytes": source.size_bytes,
                    "metadata": _json(merged_metadata),
                    "status": source.status,
                },
            )
        return await self.get_media_file(media_id, owner_user_id=owner_user_id)

    async def create_media_file(self, *, project_id: str | None, file_type: str, bucket: str, object_key: str, url: str, mime_type: str, size_bytes: int | None = None, metadata: dict[str, Any] | None = None, owner_user_id: str | None = None) -> MediaFileRecord | None:
        resolved_owner_user_id = owner_user_id
        if project_id:
            project = await self.get_project(project_id, owner_user_id=owner_user_id)
            if not project:
                return None
            resolved_owner_user_id = project.owner_user_id
        media_id = _id()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into media_files (id, project_id, owner_user_id, file_type, bucket, object_key, url, mime_type, size_bytes, metadata, status) "
                    "values (:id, :project_id, :owner_user_id, :file_type, :bucket, :object_key, :url, :mime_type, :size_bytes, :metadata, 'pending')"
                ),
                {"id": media_id, "project_id": project_id, "owner_user_id": resolved_owner_user_id, "file_type": file_type, "bucket": bucket, "object_key": object_key, "url": url, "mime_type": mime_type, "size_bytes": size_bytes, "metadata": _json(metadata or {})},
            )
        return await self.get_media_file(media_id, owner_user_id=owner_user_id)

    async def get_media_file(self, media_file_id: str, owner_user_id: str | None = None) -> MediaFileRecord | None:
        async with engine.connect() as conn:
            if owner_user_id:
                row = (
                    await conn.execute(
                        text("select * from media_files where id=:id and owner_user_id=:owner_user_id"),
                        {"id": media_file_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().first()
            else:
                row = (
                    await conn.execute(text("select * from media_files where id=:id"), {"id": media_file_id})
                ).mappings().first()
        return self._media(row) if row else None

    async def complete_media_file(self, media_file_id: str, *, width: int | None = None, height: int | None = None, duration_ms: int | None = None, size_bytes: int | None = None, metadata: dict[str, Any] | None = None, owner_user_id: str | None = None) -> MediaFileRecord | None:
        media = await self.get_media_file(media_file_id, owner_user_id=owner_user_id)
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
        return await self.get_media_file(media_file_id, owner_user_id=owner_user_id)

    async def create_generation_task(
        self,
        *,
        provider: str = "volcengine_ark",
        task_type: str,
        model_name: str,
        prompt: str,
        aspect_ratio: str,
        size: str,
        request_payload: dict[str, Any],
        owner_user_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        target_payload: dict[str, Any] | None = None,
        reference_payload: list[dict[str, Any]] | None = None,
    ) -> GenerationTaskRecord:
        task_id = _id()
        project_id = request_payload.get("project_id")
        resolved_owner_user_id = owner_user_id
        if project_id:
            project = await self.get_project(str(project_id), owner_user_id=owner_user_id)
            if project:
                resolved_owner_user_id = project.owner_user_id
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "insert into generation_tasks (id, owner_user_id, project_id, task_type, provider, model_name, status, prompt, aspect_ratio, size, request_payload, target_type, target_id, target_payload, reference_payload, images, response_payload) "
                    "values (:id, :owner_user_id, :project_id, :task_type, :provider, :model_name, 'queued', :prompt, :aspect_ratio, :size, :request_payload, :target_type, :target_id, :target_payload, :reference_payload, '[]', '{}')"
                ),
                {
                    "id": task_id,
                    "owner_user_id": resolved_owner_user_id,
                    "project_id": project_id,
                    "provider": provider,
                    "task_type": task_type,
                    "model_name": model_name,
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "size": size,
                    "request_payload": _json(request_payload),
                    "target_type": target_type,
                    "target_id": target_id,
                    "target_payload": _json(target_payload or {}),
                    "reference_payload": _json(reference_payload or []),
                },
            )
        task = await self.get_generation_task(task_id, owner_user_id=owner_user_id)
        assert task
        return task

    async def list_generation_tasks(
        self,
        *,
        owner_user_id: str | None = None,
        status: str | None = None,
        task_type: str | None = None,
        project_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        limit: int = 50,
    ) -> list[GenerationTaskRecord]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit}
        if owner_user_id:
            clauses.append("owner_user_id=:owner_user_id")
            params["owner_user_id"] = owner_user_id
        if status:
            clauses.append("status=:status")
            params["status"] = status
        if task_type:
            clauses.append("task_type=:task_type")
            params["task_type"] = task_type
        if project_id:
            clauses.append("project_id=:project_id")
            params["project_id"] = project_id
        if target_type:
            clauses.append("target_type=:target_type")
            params["target_type"] = target_type
        if target_id:
            clauses.append("target_id=:target_id")
            params["target_id"] = target_id
        where_sql = f" where {' and '.join(clauses)}" if clauses else ""
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(f"select * from generation_tasks{where_sql} order by created_at desc limit :limit"),
                    params,
                )
            ).mappings().all()
        return [self._task(row) for row in rows]

    async def get_generation_task(self, task_id: str, owner_user_id: str | None = None) -> GenerationTaskRecord | None:
        async with engine.connect() as conn:
            if owner_user_id:
                row = (
                    await conn.execute(
                        text("select * from generation_tasks where id=:id and owner_user_id=:owner_user_id"),
                        {"id": task_id, "owner_user_id": owner_user_id},
                    )
                ).mappings().first()
            else:
                row = (
                    await conn.execute(text("select * from generation_tasks where id=:id"), {"id": task_id})
                ).mappings().first()
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
        return ProjectRecord(id=row["id"], owner_user_id=row["owner_user_id"], name=row["name"], description=row["description"], aspect_ratio=row["aspect_ratio"], status=row["status"], style_prompt=row["style_prompt"] or "", style_reference_image_file_id=row["style_reference_image_file_id"], auto_apply_style_prompt=bool(row["auto_apply_style_prompt"]), auto_apply_style_reference=bool(row["auto_apply_style_reference"]), created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _script(self, row: Any) -> ScriptRecord:
        return ScriptRecord(project_id=row["project_id"], owner_user_id=row["owner_user_id"], content=row["content"], updated_at=_iso(row["updated_at"]))

    def _frame(self, row: Any) -> FrameRecord:
        return FrameRecord(id=row["id"], project_id=row["project_id"], owner_user_id=row["owner_user_id"], order_index=row["order_index"], summary=row["summary"], duration_ms=row["duration_ms"], people=row["people"], dialogue=row["dialogue"], action=row["action"], emotion=row["emotion"], note=row["note"], current_prompt=row["current_prompt"], selected_version_id=row["selected_version_id"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    async def _frame_with_versions(self, row: Any, owner_user_id: str | None = None) -> FrameRecord:
        frame = self._frame(row)
        versions = await self.list_frame_versions(frame.id, owner_user_id=owner_user_id)
        return frame.model_copy(update={"versions": versions})

    def _frame_version(self, row: Any) -> FrameVersionRecord:
        return FrameVersionRecord(id=row["id"], frame_id=row["frame_id"], owner_user_id=row["owner_user_id"], version_no=row["version_no"], image_file_id=row["image_file_id"], image_url=row["image_url"], generation_task_id=row["generation_task_id"], prompt=row["prompt"], note=row["note"], metadata=_loads(row["metadata"], {}), created_at=_iso(row["created_at"]))

    def _asset(self, row: Any) -> AssetRecord:
        return AssetRecord(id=row["id"], project_id=row["project_id"], owner_user_id=row["owner_user_id"], type=row["type"], name=row["name"], description=row["description"], default_prompt=row["default_prompt"], tags=_loads(row["tags"], []), image_file_id=row["image_file_id"], sort_order=row["sort_order"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _public_asset(self, row: Any) -> PublicAssetRecord:
        return PublicAssetRecord(id=row["id"], type=row["type"], name=row["name"], description=row["description"], default_prompt=row["default_prompt"], tags=_loads(row["tags"], []), image_file_id=row["image_file_id"], sort_order=row["sort_order"], status=row["status"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _public_asset_image(self, row: Any) -> PublicAssetImageRecord:
        created_by_name = row.get("created_by_name") if hasattr(row, "get") else None
        return PublicAssetImageRecord(id=row["id"], public_asset_id=row["public_asset_id"], media_file_id=row["media_file_id"], image_url=row["image_url"], role=row["role"], title=row["title"], description=row["description"], prompt=row["prompt"], scene_prompt=row["scene_prompt"], angle=row["angle"], tags=_loads(row["tags"], []), is_primary=bool(row["is_primary"]), sort_order=row["sort_order"], source_type=row["source_type"] or "uploaded", generation_task_id=row["generation_task_id"], generation_prompt=row["generation_prompt"] or "", created_by_user_id=row["created_by_user_id"], created_by_name=created_by_name, created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _media(self, row: Any) -> MediaFileRecord:
        return MediaFileRecord(id=row["id"], project_id=row["project_id"], owner_user_id=row["owner_user_id"], file_type=row["file_type"], bucket=row["bucket"], object_key=row["object_key"], url=row["url"], mime_type=row["mime_type"], width=row["width"], height=row["height"], duration_ms=row["duration_ms"], size_bytes=row["size_bytes"], metadata=_loads(row["metadata"], {}), status=row["status"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _task(self, row: Any) -> GenerationTaskRecord:
        return GenerationTaskRecord(id=row["id"], owner_user_id=row["owner_user_id"], status=row["status"], task_type=row["task_type"], provider=row["provider"], model_name=row["model_name"], prompt=row["prompt"], aspect_ratio=row["aspect_ratio"], size=row["size"], request_payload=_loads(row["request_payload"], {}), target_type=row["target_type"], target_id=row["target_id"], target_payload=_loads(row["target_payload"], {}), reference_payload=_loads(row["reference_payload"], []), images=_loads(row["images"], []), usage=_loads(row["usage_json"], None), response_payload=_loads(row["response_payload"], {}), error_message=row["error_message"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"]))

    def _user(self, row: Any) -> UserRecord:
        return UserRecord(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            status=row["status"],
            last_login_at=_iso(row["last_login_at"]) if row["last_login_at"] else None,
            created_at=_iso(row["created_at"]),
            updated_at=_iso(row["updated_at"]),
        )

    def _user_session(self, row: Any) -> UserSessionRecord:
        return UserSessionRecord(
            id=row["id"],
            user_id=row["user_id"],
            refresh_token_hash=row["refresh_token_hash"],
            expires_at=_iso(row["expires_at"]),
            revoked_at=_iso(row["revoked_at"]) if row["revoked_at"] else None,
            created_at=_iso(row["created_at"]),
        )

    def _user_mcp_token(self, row: Any) -> UserMcpTokenRecord:
        return UserMcpTokenRecord(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            token_hash=row["token_hash"],
            last_used_at=_iso(row["last_used_at"]) if row["last_used_at"] else None,
            revoked_at=_iso(row["revoked_at"]) if row["revoked_at"] else None,
            created_at=_iso(row["created_at"]),
        )


store = DatabaseStore()
