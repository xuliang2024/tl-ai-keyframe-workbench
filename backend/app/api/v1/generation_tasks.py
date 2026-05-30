import base64
from dataclasses import dataclass
import re
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
import httpx

from app.core.config import settings
from app.integrations.apiz_generation import ApizGenerationClient, ApizGenerationError
from app.integrations.object_storage import ObjectStorageError, get_object_storage_client
from app.schemas.generation_task import GenerationTaskCreate, GenerationTaskResponse
from app.services.memory_store import GenerationTaskRecord
from app.services.database_store import store
from app.services.image_prompt_requirements import compose_image_prompt

router = APIRouter()


@dataclass(frozen=True)
class PreparedGenerationRequest:
    payload: GenerationTaskCreate
    task_type: str
    prompt: str
    image: str | list[str] | None
    request_payload: dict[str, Any]


@router.post("")
async def create_generation_task(
    payload: GenerationTaskCreate,
    background_tasks: BackgroundTasks,
) -> GenerationTaskResponse:
    prepared = await _prepare_generation_request(payload)

    size = prepared.payload.size or settings.image_generation_size
    model_name = _model_name_for_task(prepared.task_type)
    task = await store.create_generation_task(
        provider="apiz",
        task_type=prepared.task_type,
        model_name=model_name,
        prompt=prepared.prompt,
        aspect_ratio=prepared.payload.aspect_ratio,
        size=size,
        request_payload=prepared.request_payload,
    )
    background_tasks.add_task(_run_generation_task, task.id)
    return _task_response(task)


async def _prepare_generation_request(payload: GenerationTaskCreate) -> PreparedGenerationRequest:
    payload = await _resolve_project_from_frame(payload)
    prepared_prompt = await _compose_prompt_for_image_type(payload)
    asset_references = await _collect_keyframe_asset_references(payload)
    prompt_with_references = _append_asset_reference_guidance(prepared_prompt, asset_references)
    image_with_references = _merge_image_inputs(
        payload.image,
        [reference["url"] for reference in asset_references],
    )
    final_prompt, final_image = await _apply_project_style(
        project_id=payload.project_id,
        prompt=prompt_with_references,
        image=image_with_references,
        apply_style_prompt=payload.image_type is None,
        apply_style_reference=payload.image_type in ("scene", "keyframe") or payload.image_type is None,
    )

    task_type = payload.task_type or ("image_to_image" if final_image else "text_to_image")
    if task_type == "text_to_image" and final_image:
        task_type = "image_to_image"
    if task_type in ("image_to_image", "image_edit") and not final_image:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="image is required for image_to_image and image_edit tasks",
        )

    request_payload = {
        "task_type": task_type,
        "image": final_image,
        "output_format": settings.image_generation_output_format or None,
        "response_format": "url",
        "watermark": payload.watermark,
        "project_id": payload.project_id,
        "frame_id": payload.frame_id,
        "asset_ids": payload.asset_ids,
        "auto_apply_asset_references": payload.auto_apply_asset_references,
        "reference_assets": asset_references,
        "image_type": payload.image_type,
    }
    return PreparedGenerationRequest(
        payload=payload,
        task_type=task_type,
        prompt=final_prompt,
        image=final_image,
        request_payload=request_payload,
    )


async def _resolve_project_from_frame(payload: GenerationTaskCreate) -> GenerationTaskCreate:
    if not payload.frame_id:
        return payload

    frame = await store.get_frame(payload.frame_id)
    if not frame:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="frame_id not found")
    if payload.project_id and payload.project_id != frame.project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="frame_id does not belong to project_id",
        )
    return payload.model_copy(update={"project_id": payload.project_id or frame.project_id})


async def _compose_prompt_for_image_type(payload: GenerationTaskCreate) -> str:
    if not payload.image_type:
        return payload.prompt

    project_style_prompt = None
    if payload.project_id:
        project = await store.get_project(payload.project_id)
        if project and project.auto_apply_style_prompt:
            project_style_prompt = project.style_prompt

    try:
        return compose_image_prompt(
            image_type=payload.image_type,
            prompt=payload.prompt,
            project_style_prompt=project_style_prompt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


async def _apply_project_style(
    *,
    project_id: str | None,
    prompt: str,
    image: str | list[str] | None,
    apply_style_prompt: bool = True,
    apply_style_reference: bool = True,
) -> tuple[str, str | list[str] | None]:
    if not project_id:
        return prompt, image

    project = await store.get_project(project_id)
    if not project:
        return prompt, image

    final_prompt = prompt
    if apply_style_prompt and project.auto_apply_style_prompt and project.style_prompt.strip():
        final_prompt = f"{prompt}\n风格提示词：{project.style_prompt.strip()}"

    final_image = image
    if apply_style_reference and project.auto_apply_style_reference and project.style_reference_image_file_id:
        media_file = await store.get_media_file(project.style_reference_image_file_id)
        if media_file and media_file.url:
            image_items = image if isinstance(image, list) else ([image] if image else [])
            final_image = [*image_items, media_file.url]

    return final_prompt, final_image


async def _collect_keyframe_asset_references(payload: GenerationTaskCreate) -> list[dict[str, str]]:
    if payload.image_type != "keyframe" or not payload.auto_apply_asset_references:
        return []

    assets = []
    if payload.asset_ids:
        for asset_id in payload.asset_ids:
            asset = await store.get_asset(asset_id)
            if not asset:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"asset_id not found: {asset_id}")
            if payload.project_id and asset.project_id != payload.project_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"asset_id does not belong to project_id: {asset_id}",
                )
            assets.append(asset)
    elif payload.project_id:
        assets = await store.list_assets(payload.project_id)

    references: list[dict[str, str]] = []
    for asset in assets:
        if not asset.image_file_id:
            continue
        media_file = await store.get_media_file(asset.image_file_id)
        if not media_file or not media_file.url:
            continue
        references.append(
            {
                "asset_id": asset.id,
                "name": asset.name,
                "type": asset.type,
                "image_file_id": asset.image_file_id,
                "url": media_file.url,
            }
        )
    return references


def _append_asset_reference_guidance(prompt: str, references: list[dict[str, str]]) -> str:
    if not references:
        return prompt

    lines = [
        prompt,
        "",
        "[Asset reference requirements]",
        "Use the attached asset reference images as identity and design anchors. Only show an asset when the shot prompt calls for it; do not force every reference into the frame. Keep each referenced character's face, hairstyle, costume silhouette, robot structure, prop shape, material, and color consistent with its matching reference. Do not merge different reference assets into one object or redesign them.",
    ]
    for reference in references:
        lines.append(f"- {reference['type']} / {reference['name']}: preserve this asset's visual identity from its reference image.")
    return "\n".join(lines)


def _merge_image_inputs(
    image: str | list[str] | None,
    reference_urls: list[str],
) -> str | list[str] | None:
    image_items = image if isinstance(image, list) else ([image] if image else [])
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*image_items, *reference_urls]:
        if item and item not in seen:
            merged.append(item)
            seen.add(item)
    if not merged:
        return None
    if len(merged) == 1:
        return merged[0]
    return merged


@router.get("/{task_id}")
async def get_generation_task(task_id: str) -> GenerationTaskResponse:
    task = await store.get_generation_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="generation task not found")
    return _task_response(task)


@router.post("/{task_id}/retry")
async def retry_generation_task(
    task_id: str,
    background_tasks: BackgroundTasks,
) -> GenerationTaskResponse:
    task = await store.get_generation_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="generation task not found")
    if task.status in ("queued", "running"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="generation task is already running",
        )

    updated = await store.update_generation_task(
        task_id,
        status="queued",
        images=[],
        response_payload={},
        error_message="",
    )
    background_tasks.add_task(_run_generation_task, task_id)
    return _task_response(updated or task)


@router.post("/{task_id}/cancel")
async def cancel_generation_task(task_id: str) -> GenerationTaskResponse:
    task = await store.get_generation_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="generation task not found")
    if task.status in ("succeeded", "failed", "canceled"):
        return _task_response(task)

    updated = await store.update_generation_task(task_id, status="canceled")
    return _task_response(updated or task)


async def _run_generation_task(task_id: str) -> None:
    task = await store.get_generation_task(task_id)
    if not task or task.status == "canceled":
        return

    await store.update_generation_task(task_id, status="running")
    request_payload = task.request_payload
    task_type = request_payload.get("task_type")

    client = ApizGenerationClient(
        api_key=settings.apiz_api_key,
        base_url=settings.apiz_base_url,
        poll_interval_seconds=settings.apiz_poll_interval_seconds,
        max_poll_attempts=settings.apiz_max_poll_attempts,
    )

    try:
        if task_type in ("text_to_video", "frames_to_video"):
            response_payload = await client.generate_video(
                model=task.model_name,
                prompt=task.prompt,
                image=request_payload.get("image"),
                ratio=task.aspect_ratio,
                duration=settings.apiz_video_duration_seconds,
                resolution=settings.apiz_video_resolution,
                engine_model=settings.apiz_video_engine_model,
            )
            await _mark_generation_succeeded(task_id, response_payload, [])
            return

        response_payload = await client.generate_image(
            model=task.model_name,
            prompt=task.prompt,
            image=request_payload.get("image"),
            image_size=task.aspect_ratio,
            resolution=task.size,
            quality=settings.apiz_image_quality,
            num_images=settings.apiz_image_num_images,
            output_format=request_payload.get("output_format") or "png",
        )
    except ApizGenerationError as exc:
        await _mark_generation_failed(task_id, str(exc))
        return

    try:
        persisted_images = await _persist_generated_images(task_id, response_payload, request_payload)
    except (ObjectStorageError, httpx.HTTPError, ValueError) as exc:
        await _mark_generation_failed(task_id, f"generated image transfer failed: {exc}")
        return

    await _mark_generation_succeeded(task_id, response_payload, persisted_images)


def _model_name_for_task(task_type: str) -> str:
    if task_type == "text_to_image":
        return settings.apiz_text_to_image_model
    if task_type in ("image_to_image", "image_edit"):
        return settings.apiz_image_edit_model
    return settings.apiz_video_model


async def _persist_generated_images(
    task_id: str,
    response_payload: dict[str, Any],
    request_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    images = response_payload.get("data") or []
    if not images:
        return []

    project_id = request_payload.get("project_id")
    output_format = request_payload.get("output_format") or "png"
    extension = "jpg" if output_format == "jpeg" else output_format
    content_type = "image/jpeg" if output_format == "jpeg" else "image/png"
    storage = get_object_storage_client()
    persisted_images: list[dict[str, Any]] = []

    for index, image in enumerate(images):
        image_bytes, detected_content_type = await _generated_image_bytes(image)
        final_content_type = detected_content_type or content_type
        object_key = _generated_image_object_key(
            task_id=task_id,
            project_id=project_id,
            index=index,
            extension=_extension_for_content_type(final_content_type, extension),
        )
        public_url = storage.upload_bytes(object_key, image_bytes, final_content_type)
        media_file = await store.create_media_file(
            project_id=project_id,
            file_type="image",
            bucket=storage.bucket,
            object_key=object_key,
            url=public_url,
            mime_type=final_content_type,
            size_bytes=len(image_bytes),
            metadata={
                "generation_task_id": task_id,
                "source_size": image.get("size"),
            },
        )
        if not media_file:
            raise ValueError("Project not found")
        completed_media_file = await store.complete_media_file(media_file.id, size_bytes=len(image_bytes))
        persisted_images.append(
            {
                "url": public_url,
                "size": image.get("size"),
                "media_file_id": completed_media_file.id if completed_media_file else media_file.id,
                "object_key": object_key,
            }
        )

    return persisted_images


async def _generated_image_bytes(image: dict[str, Any]) -> tuple[bytes, str | None]:
    b64_json = image.get("b64_json")
    if b64_json:
        normalized = str(b64_json).split(",", 1)[-1]
        return base64.b64decode(normalized), None

    url = image.get("url")
    if not url:
        raise ValueError("generated image result is missing url or b64_json")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
    return response.content, response.headers.get("content-type")


def _generated_image_object_key(
    *,
    task_id: str,
    project_id: str | None,
    index: int,
    extension: str,
) -> str:
    now = datetime.now(UTC)
    clean_task_id = re.sub(r"[^a-zA-Z0-9-]+", "-", task_id)
    return "/".join(
        part.strip("/")
        for part in (
            settings.media_upload_prefix,
            project_id or "unassigned",
            "generated",
            "images",
            f"{now:%Y}",
            f"{now:%m}",
            f"{now:%d}",
            f"{clean_task_id}-{index + 1}.{extension}",
        )
    )


def _extension_for_content_type(content_type: str, fallback: str) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    if normalized == "image/jpeg":
        return "jpg"
    if normalized == "image/png":
        return "png"
    if normalized == "image/webp":
        return "webp"
    return fallback


async def _mark_generation_succeeded(
    task_id: str,
    response_payload: dict[str, Any],
    images: list[dict[str, Any]],
) -> None:
    public_response_payload = {**response_payload, "data": images}
    await store.update_generation_task(
        task_id,
        status="succeeded",
        images=images,
        usage=response_payload.get("usage"),
        response_payload=public_response_payload,
    )


async def _mark_generation_failed(task_id: str, error_message: str) -> None:
    await store.update_generation_task(
        task_id,
        status="failed",
        error_message=error_message,
        response_payload={"error": {"message": error_message}},
    )


def _task_response(task: GenerationTaskRecord) -> GenerationTaskResponse:
    return GenerationTaskResponse(
        task_id=task.id,
        status=task.status,
        task_type=task.task_type,
        provider=task.provider,
        model_name=task.model_name,
        prompt=task.prompt,
        aspect_ratio=task.aspect_ratio,
        size=task.size,
        images=task.images,
        usage=task.usage,
        response_payload=task.response_payload,
        error_message=task.error_message or None,
    )
