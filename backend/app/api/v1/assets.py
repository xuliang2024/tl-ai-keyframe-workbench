from fastapi import APIRouter, HTTPException

from app.schemas.asset import AssetCreate, AssetList, AssetRead, AssetUpdate
from app.services.database_store import store

router = APIRouter()


@router.get("/projects/{project_id}/assets", response_model=AssetList)
async def list_assets(project_id: str) -> AssetList:
    if not await store.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return AssetList(
        project_id=project_id,
        items=[await _asset_read(asset) for asset in await store.list_assets(project_id)],
    )


@router.post("/projects/{project_id}/assets", response_model=AssetRead, status_code=201)
async def create_asset(project_id: str, payload: AssetCreate) -> AssetRead:
    asset = await store.create_asset(
        project_id=project_id,
        name=payload.name,
        type=payload.type,
        description=payload.description,
        default_prompt=payload.default_prompt,
        tags=payload.tags,
        image_file_id=payload.image_file_id,
        sort_order=payload.sort_order,
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Project not found")
    return await _asset_read(asset)


@router.patch("/assets/{asset_id}", response_model=AssetRead)
async def update_asset(asset_id: str, payload: AssetUpdate) -> AssetRead:
    asset = await store.update_asset(asset_id, payload.model_dump(exclude_unset=True))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return await _asset_read(asset)


@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(asset_id: str) -> None:
    deleted = await store.delete_asset(asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")


async def _asset_read(asset) -> AssetRead:
    image_url = None
    if asset.image_file_id:
        media_file = await store.get_media_file(asset.image_file_id)
        image_url = media_file.url if media_file else None
    return AssetRead.model_validate(asset).model_copy(update={"image_url": image_url})
