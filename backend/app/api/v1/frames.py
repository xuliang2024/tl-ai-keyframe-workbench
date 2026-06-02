from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.schemas.frame import (
    FrameCreate,
    FrameList,
    FrameRead,
    FrameUpdate,
    FrameVersionCreate,
    FrameVersionRead,
    FrameVersionSelect,
)
from app.services.database_store import store
from app.services.memory_store import UserRecord

router = APIRouter()


@router.get("/projects/{project_id}/frames", response_model=FrameList)
async def list_frames(
    project_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> FrameList:
    if not await store.get_project(project_id, owner_user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Project not found")
    return FrameList(
        project_id=project_id,
        items=[
            FrameRead.model_validate(frame)
            for frame in await store.list_frames(project_id, owner_user_id=current_user.id)
        ],
    )


@router.post("/projects/{project_id}/frames", response_model=FrameRead, status_code=201)
async def create_frame(
    project_id: str,
    payload: FrameCreate,
    current_user: UserRecord = Depends(get_current_user),
) -> FrameRead:
    frame = await store.create_frame(
        project_id=project_id,
        summary=payload.summary,
        order_index=payload.order_index,
        duration_ms=payload.duration_ms,
        current_prompt=payload.current_prompt,
        owner_user_id=current_user.id,
    )
    if not frame:
        raise HTTPException(status_code=404, detail="Project not found")
    return FrameRead.model_validate(frame)


@router.patch("/frames/{frame_id}", response_model=FrameRead)
async def update_frame(
    frame_id: str,
    payload: FrameUpdate,
    current_user: UserRecord = Depends(get_current_user),
) -> FrameRead:
    values = payload.model_dump(exclude_unset=True)
    frame = await store.update_frame(frame_id, values, owner_user_id=current_user.id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    return FrameRead.model_validate(frame)


@router.delete("/frames/{frame_id}")
async def delete_frame(
    frame_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> dict[str, str]:
    deleted = await store.delete_frame(frame_id, owner_user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Frame not found")
    return {"frame_id": frame_id, "status": "deleted"}


@router.post("/frames/{frame_id}/versions", response_model=FrameVersionRead, status_code=201)
async def create_frame_version(
    frame_id: str,
    payload: FrameVersionCreate,
    current_user: UserRecord = Depends(get_current_user),
) -> FrameVersionRead:
    version = await store.create_frame_version(
        frame_id=frame_id,
        image_file_id=payload.image_file_id,
        generation_task_id=payload.generation_task_id,
        prompt=payload.prompt,
        note=payload.note,
        metadata=payload.metadata,
        select=payload.select,
        owner_user_id=current_user.id,
    )
    if not version:
        raise HTTPException(status_code=404, detail="Frame or image file not found")
    return FrameVersionRead.model_validate(version)


@router.post("/frames/{frame_id}/versions/select", response_model=FrameRead)
async def select_frame_version(
    frame_id: str,
    payload: FrameVersionSelect,
    current_user: UserRecord = Depends(get_current_user),
) -> FrameRead:
    frame = await store.select_frame_version(
        frame_id,
        payload.version_id,
        owner_user_id=current_user.id,
    )
    if not frame:
        raise HTTPException(status_code=404, detail="Frame version not found")
    return FrameRead.model_validate(frame)
