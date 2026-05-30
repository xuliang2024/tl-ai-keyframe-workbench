import mimetypes
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.integrations.object_storage import ObjectStorageError, get_object_storage_client
from app.schemas.media import (
    MediaFileRead,
    MediaUploadComplete,
    MediaUploadUrlCreate,
    MediaUploadUrlRead,
)
from app.services.database_store import store

router = APIRouter()


@router.post("/upload", response_model=MediaUploadUrlRead)
@router.post("/upload-url", response_model=MediaUploadUrlRead)
async def create_upload_url(payload: MediaUploadUrlCreate) -> MediaUploadUrlRead:
    _validate_upload_size(payload.file_type, payload.size_bytes)

    storage = get_object_storage_client()
    object_key = _build_object_key(payload)
    public_url = storage.public_url(object_key)

    media_file = await store.create_media_file(
        project_id=payload.project_id,
        file_type=payload.file_type,
        bucket=storage.bucket,
        object_key=object_key,
        url=public_url,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        metadata={
            "original_filename": payload.filename,
            **payload.metadata,
        },
    )
    if not media_file:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        upload_url = storage.generate_presigned_put_url(
            object_key,
            expires_in=settings.media_presign_expires_seconds,
        )
    except ObjectStorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return MediaUploadUrlRead(
        media_file_id=media_file.id,
        file_type=media_file.file_type,
        bucket=media_file.bucket,
        object_key=media_file.object_key,
        upload_url=upload_url,
        upload_headers={"Content-Type": media_file.mime_type},
        public_url=media_file.url,
        expires_in=settings.media_presign_expires_seconds,
    )


@router.post("/{media_file_id}/complete", response_model=MediaFileRead)
async def complete_upload(media_file_id: str, payload: MediaUploadComplete) -> MediaFileRead:
    media_file = await store.complete_media_file(
        media_file_id,
        width=payload.width,
        height=payload.height,
        duration_ms=payload.duration_ms,
        size_bytes=payload.size_bytes,
        metadata=payload.metadata,
    )
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    return MediaFileRead.model_validate(media_file)


@router.get("/{media_file_id}", response_model=MediaFileRead)
async def get_media_file(media_file_id: str) -> MediaFileRead:
    media_file = await store.get_media_file(media_file_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
    return MediaFileRead.model_validate(media_file)


def _validate_upload_size(file_type: str, size_bytes: int | None) -> None:
    if size_bytes is None:
        return

    if file_type == "image" and size_bytes > settings.max_image_upload_bytes:
        raise HTTPException(status_code=413, detail="Image file is too large")

    if file_type == "video" and size_bytes > settings.max_video_upload_bytes:
        raise HTTPException(status_code=413, detail="Video file is too large")


def _build_object_key(payload: MediaUploadUrlCreate) -> str:
    now = datetime.now(UTC)
    extension = _file_extension(payload.filename, payload.mime_type)
    safe_stem = _safe_filename_stem(payload.filename)
    unique_name = f"{uuid4().hex}-{safe_stem}{extension}"
    return "/".join(
        part.strip("/")
        for part in (
            settings.media_upload_prefix,
            payload.project_id or "unassigned",
            f"{payload.file_type}s",
            f"{now:%Y}",
            f"{now:%m}",
            f"{now:%d}",
            unique_name,
        )
        if part.strip("/")
    )


def _safe_filename_stem(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9._-]+", "-", stem).strip(".-_")
    return stem[:80] or "file"


def _file_extension(filename: str, mime_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix and re.fullmatch(r"\.[a-z0-9]{1,12}", suffix):
        return suffix

    guessed = mimetypes.guess_extension(mime_type)
    if guessed:
        return ".jpg" if guessed == ".jpe" else guessed
    return ""
