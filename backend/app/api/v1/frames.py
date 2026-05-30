from fastapi import APIRouter, HTTPException

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

router = APIRouter()


@router.get("/projects/{project_id}/frames", response_model=FrameList)
async def list_frames(project_id: str) -> FrameList:
    if not await store.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return FrameList(
        project_id=project_id,
        items=[FrameRead.model_validate(frame) for frame in await store.list_frames(project_id)],
    )


@router.post("/projects/{project_id}/frames", response_model=FrameRead, status_code=201)
async def create_frame(project_id: str, payload: FrameCreate) -> FrameRead:
    frame = await store.create_frame(
        project_id=project_id,
        summary=payload.summary,
        order_index=payload.order_index,
        duration_ms=payload.duration_ms,
        current_prompt=payload.current_prompt,
    )
    if not frame:
        raise HTTPException(status_code=404, detail="Project not found")
    return FrameRead.model_validate(frame)


@router.patch("/frames/{frame_id}", response_model=FrameRead)
async def update_frame(frame_id: str, payload: FrameUpdate) -> FrameRead:
    values = payload.model_dump(exclude_unset=True)
    frame = await store.update_frame(frame_id, values)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    return FrameRead.model_validate(frame)


@router.delete("/frames/{frame_id}")
async def delete_frame(frame_id: str) -> dict[str, str]:
    deleted = await store.delete_frame(frame_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Frame not found")
    return {"frame_id": frame_id, "status": "deleted"}


@router.post("/frames/{frame_id}/versions", response_model=FrameVersionRead, status_code=201)
async def create_frame_version(frame_id: str, payload: FrameVersionCreate) -> FrameVersionRead:
    version = await store.create_frame_version(
        frame_id=frame_id,
        image_file_id=payload.image_file_id,
        generation_task_id=payload.generation_task_id,
        prompt=payload.prompt,
        note=payload.note,
        metadata=payload.metadata,
        select=payload.select,
    )
    if not version:
        raise HTTPException(status_code=404, detail="Frame or image file not found")
    return FrameVersionRead.model_validate(version)


@router.post("/frames/{frame_id}/versions/select", response_model=FrameRead)
async def select_frame_version(frame_id: str, payload: FrameVersionSelect) -> FrameRead:
    frame = await store.select_frame_version(frame_id, payload.version_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame version not found")
    return FrameRead.model_validate(frame)
