from fastapi import APIRouter, HTTPException

from app.schemas.script import ScriptRead, ScriptUpdate
from app.services.database_store import store

router = APIRouter()


@router.get("/projects/{project_id}/script", response_model=ScriptRead)
async def get_project_script(project_id: str) -> ScriptRead:
    script = await store.get_script(project_id)
    if not script:
        raise HTTPException(status_code=404, detail="Project script not found")
    return ScriptRead.model_validate(script)


@router.put("/projects/{project_id}/script", response_model=ScriptRead)
async def update_project_script(project_id: str, payload: ScriptUpdate) -> ScriptRead:
    script = await store.update_script(project_id, payload.content)
    if not script:
        raise HTTPException(status_code=404, detail="Project not found")
    return ScriptRead.model_validate(script)


@router.delete("/projects/{project_id}/script", status_code=204)
async def delete_project_script(project_id: str) -> None:
    script = await store.clear_script(project_id)
    if not script:
        raise HTTPException(status_code=404, detail="Project not found")
