import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.integrations.object_storage import get_object_storage_client
from app.schemas.asset import AssetRead
from app.schemas.public_asset import (
    PublicAssetImageCreate,
    PublicAssetImageList,
    PublicAssetImageRead,
    PublicAssetImportCreate,
    PublicAssetImportError,
    PublicAssetImportResult,
    PublicAssetList,
    PublicAssetRead,
)
from app.services.database_store import store
from app.services.memory_store import UserRecord

router = APIRouter()


@router.get("/public-assets", response_model=PublicAssetList)
async def list_public_assets(
    type: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    current_user: UserRecord = Depends(get_current_user),
) -> PublicAssetList:
    del current_user
    return PublicAssetList(
        items=[
            await _public_asset_read(asset)
            for asset in await store.list_public_assets(type=type, keyword=keyword)
        ]
    )


@router.get("/public-assets/{public_asset_id}", response_model=PublicAssetRead)
async def get_public_asset(
    public_asset_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> PublicAssetRead:
    del current_user
    public_asset = await store.get_public_asset(public_asset_id)
    if not public_asset:
        raise HTTPException(status_code=404, detail="Public asset not found")
    return await _public_asset_read(public_asset)


@router.get("/public-assets/{public_asset_id}/images", response_model=PublicAssetImageList)
async def list_public_asset_images(
    public_asset_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> PublicAssetImageList:
    del current_user
    if not await store.get_public_asset(public_asset_id):
        raise HTTPException(status_code=404, detail="Public asset not found")
    images = await _public_asset_images_with_primary_fallback(public_asset_id)
    return PublicAssetImageList(public_asset_id=public_asset_id, items=images)


@router.post("/public-assets/{public_asset_id}/images", response_model=PublicAssetImageRead, status_code=201)
async def create_public_asset_image(
    public_asset_id: str,
    payload: PublicAssetImageCreate,
    current_user: UserRecord = Depends(get_current_user),
) -> PublicAssetImageRead:
    image = await store.create_public_asset_image(
        public_asset_id=public_asset_id,
        media_file_id=payload.media_file_id,
        role=payload.role,
        title=payload.title,
        description=payload.description,
        prompt=payload.prompt,
        scene_prompt=payload.scene_prompt,
        angle=payload.angle,
        tags=payload.tags,
        is_primary=payload.is_primary,
        sort_order=payload.sort_order,
        source_type=payload.source_type,
        generation_task_id=payload.generation_task_id,
        generation_prompt=payload.generation_prompt,
        created_by_user_id=current_user.id,
    )
    if not image:
        raise HTTPException(status_code=404, detail="Public asset or media file not found")
    return PublicAssetImageRead.model_validate(image)


@router.delete("/public-assets/images/{image_id}", status_code=204)
async def delete_public_asset_image(
    image_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> None:
    del current_user
    deleted = await store.delete_public_asset_image(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Public asset image not found")


@router.post("/projects/{project_id}/assets/import-public", response_model=PublicAssetImportResult)
async def import_public_assets(
    project_id: str,
    payload: PublicAssetImportCreate,
    current_user: UserRecord = Depends(get_current_user),
) -> PublicAssetImportResult:
    if not await store.get_project(project_id, owner_user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Project not found")

    imported: list[AssetRead] = []
    errors: list[PublicAssetImportError] = []
    existing_assets = await store.list_assets(project_id, owner_user_id=current_user.id)
    sort_order = len(existing_assets)

    for public_asset_id in payload.public_asset_ids:
        public_asset = await store.get_public_asset(public_asset_id)
        if not public_asset:
            errors.append(PublicAssetImportError(public_asset_id=public_asset_id, detail="Public asset not found"))
            continue

        image_file_id = None
        if public_asset.image_file_id:
            copied_media = await _copy_public_asset_media(
                public_asset_id=public_asset.id,
                source_media_file_id=public_asset.image_file_id,
                project_id=project_id,
                owner_user_id=current_user.id,
                copy_media=payload.copy_media,
            )
            if not copied_media:
                errors.append(PublicAssetImportError(public_asset_id=public_asset_id, detail="Asset image copy failed"))
                continue
            image_file_id = copied_media.id

        asset = await store.create_asset(
            project_id=project_id,
            name=public_asset.name,
            type=public_asset.type,
            description=public_asset.description,
            default_prompt=public_asset.default_prompt,
            tags=[*public_asset.tags],
            image_file_id=image_file_id,
            sort_order=sort_order,
            owner_user_id=current_user.id,
        )
        if not asset:
            errors.append(PublicAssetImportError(public_asset_id=public_asset_id, detail="Asset import failed"))
            continue

        sort_order += 1
        imported.append(await _asset_read(asset, owner_user_id=current_user.id))

    return PublicAssetImportResult(project_id=project_id, items=imported, errors=errors)


async def _copy_public_asset_media(
    *,
    public_asset_id: str,
    source_media_file_id: str,
    project_id: str,
    owner_user_id: str,
    copy_media: bool,
):
    source = await store.get_media_file(source_media_file_id)
    if not source:
        return None

    target_key = _build_copied_media_key(project_id, source.object_key, source.mime_type)
    target_url = source.url
    copy_mode = "record_only"
    if copy_media and source.object_key:
        try:
            target_url = get_object_storage_client().copy_object(source.object_key, target_key)
            copy_mode = "object_copy"
        except Exception:
            target_url = source.url
            target_key = source.object_key

    return await store.copy_media_file_record_to_project(
        source_media_file_id=source.id,
        project_id=project_id,
        owner_user_id=owner_user_id,
        object_key=target_key,
        url=target_url,
        metadata={
            "usage": "asset",
            "copied_from_public_asset_id": public_asset_id,
            "copy_mode": copy_mode,
        },
    )


def _build_copied_media_key(project_id: str, source_key: str, mime_type: str) -> str:
    now = datetime.now(UTC)
    suffix = Path(source_key).suffix
    if not suffix:
        suffix = mimetypes.guess_extension(mime_type) or ""
    return "/".join(
        part.strip("/")
        for part in (
            settings.media_upload_prefix,
            project_id,
            "assets",
            f"{now:%Y}",
            f"{now:%m}",
            f"{now:%d}",
            f"{uuid4().hex}{suffix}",
        )
        if part.strip("/")
    )


async def _public_asset_read(asset) -> PublicAssetRead:
    image_url = None
    if asset.image_file_id:
        media_file = await store.get_media_file(asset.image_file_id)
        image_url = media_file.url if media_file else None
    return PublicAssetRead.model_validate(asset).model_copy(update={"image_url": image_url})


async def _public_asset_images_with_primary_fallback(public_asset_id: str) -> list[PublicAssetImageRead]:
    images = [
        PublicAssetImageRead.model_validate(image)
        for image in await store.list_public_asset_images(public_asset_id)
    ]
    if images:
        return images

    asset = await store.get_public_asset(public_asset_id)
    if not asset or not asset.image_file_id:
        return []
    media_file = await store.get_media_file(asset.image_file_id)
    if not media_file:
        return []
    return [
        PublicAssetImageRead(
            id=f"primary-{asset.id}",
            public_asset_id=asset.id,
            media_file_id=media_file.id,
            image_url=media_file.url,
            role="primary",
            title="主图",
            description=asset.description,
            prompt=asset.default_prompt,
            scene_prompt="",
            angle="",
            tags=asset.tags,
            is_primary=True,
            sort_order=0,
            source_type="uploaded",
            generation_task_id=None,
            generation_prompt="",
            created_by_user_id=None,
            created_by_name=None,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )
    ]


async def _asset_read(asset, owner_user_id: str | None = None) -> AssetRead:
    image_url = None
    if asset.image_file_id:
        media_file = await store.get_media_file(asset.image_file_id, owner_user_id=owner_user_id)
        image_url = media_file.url if media_file else None
    return AssetRead.model_validate(asset).model_copy(update={"image_url": image_url})
