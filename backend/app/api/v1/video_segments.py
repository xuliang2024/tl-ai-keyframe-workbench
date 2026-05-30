from fastapi import APIRouter

router = APIRouter()


@router.get("/projects/{project_id}/video-segments")
async def list_video_segments(project_id: str) -> dict[str, object]:
    return {"project_id": project_id, "items": []}
