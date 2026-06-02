import os
import re
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FrameLab API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    public_api_base_url: str = "http://127.0.0.1:8000"
    site_public_base_url: str = "http://127.0.0.1:4173"
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:4174",
            "http://127.0.0.1:4174",
        ]
    )

    database_url: str = "mysql+asyncmy://user:pass@127.0.0.1:3306/keyframe_workbench?charset=utf8mb4"
    redis_url: str = "redis://localhost:6379/0"
    auth_secret_key: str = "change-me-in-production"
    auth_access_token_expires_minutes: int = 525600
    auth_refresh_token_expires_days: int = 3650

    storage_provider: str = "local"
    storage_bucket: str = "tl-keyframe"
    storage_region: str = ""
    storage_endpoint: str = ""
    storage_public_base_url: str = "http://127.0.0.1:8000/uploads"
    storage_cdn_cname: str = ""
    storage_image_prefix: str = "generated/images"
    storage_video_prefix: str = "generated/videos"

    site_storage_bucket: str = ""
    site_storage_public_base_url: str = ""
    site_storage_cdn_cname: str = ""
    tos_access_key_id: str = ""
    tos_secret_access_key: str = ""
    media_upload_prefix: str = "media"
    media_presign_expires_seconds: int = 900
    max_image_upload_bytes: int = 25 * 1024 * 1024
    max_video_upload_bytes: int = 1024 * 1024 * 1024

    openai_api_key: str = ""
    seedance_api_key: str = ""
    ark_api_key: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://codex.apiz.ai/v1"
    llm_model: str = "GPT-5.5"
    llm_timeout_seconds: float = 120
    volcengine_ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volcengine_image_model: str = "doubao-seedream-5-0-260128"
    apiz_api_key: str = ""
    apiz_base_url: str = "https://api.apiz.ai/api/v3"
    apiz_text_to_image_model: str = "openai/gpt-image-2"
    apiz_image_edit_model: str = "openai/gpt-image-2/edit"
    apiz_video_model: str = "st-ai/super-seed2-lite"
    apiz_image_quality: str = "high"
    apiz_image_num_images: int = 1
    apiz_video_engine_model: str = "seedance2.0_fast_direct"
    apiz_video_duration_seconds: int = 4
    apiz_video_resolution: str = "720p"
    apiz_poll_interval_seconds: float = 2
    apiz_max_poll_attempts: int = 90
    image_generation_size: str = "4K"
    image_generation_response_format: str = "b64_json"
    image_generation_output_format: str = "png"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def resolve_ark_api_key() -> str:
    if settings.ark_api_key:
        return settings.ark_api_key

    for env_name in ("ARK_API_KEY", "VOLCENGINE_ARK_API_KEY", "FANGZHOU_API_KEY"):
        env_value = os.getenv(env_name)
        if env_value:
            return env_value

    for env_path in _candidate_env_files():
        if not env_path.exists():
            continue
        key = _extract_ark_key(env_path.read_text(encoding="utf-8"))
        if key:
            return key

    return ""


def _candidate_env_files() -> tuple[Path, ...]:
    repo_root = Path(__file__).resolve().parents[3]
    return (
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        repo_root / ".env",
        repo_root / "backend" / ".env",
    )


def _extract_ark_key(env_text: str) -> str:
    standard_names = {"ARK_API_KEY", "VOLCENGINE_ARK_API_KEY", "FANGZHOU_API_KEY"}
    for line in env_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            name, value = line.split("=", 1)
            if name.strip() in standard_names and value.strip():
                return value.strip().strip("'\"")

        match = re.search(r"ark-[A-Za-z0-9-]+", line)
        if match:
            return match.group(0)

    return ""
