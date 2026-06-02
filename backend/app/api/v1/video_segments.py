from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.services.database_store import store
from app.services.memory_store import UserRecord

router = APIRouter()


@router.get("/projects/{project_id}/video-segments")
async def list_video_segments(
    project_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> dict[str, object]:
    if not await store.get_project(project_id, owner_user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "items": []}
