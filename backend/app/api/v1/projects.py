from fastapi import APIRouter, HTTPException

from app.schemas.project import ProjectCreate, ProjectList, ProjectRead, ProjectUpdate
from app.services.database_store import store

router = APIRouter()


@router.get("", response_model=ProjectList)
async def list_projects() -> ProjectList:
    return ProjectList(items=[await _project_read(project) for project in await store.list_projects()])


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(payload: ProjectCreate) -> ProjectRead:
    project = await store.create_project(
        name=payload.name,
        description=payload.description,
        aspect_ratio=payload.aspect_ratio,
    )
    return await _project_read(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: str) -> ProjectRead:
    project = await store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await _project_read(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(project_id: str, payload: ProjectUpdate) -> ProjectRead:
    project = await store.update_project(project_id, payload.model_dump(exclude_unset=True))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await _project_read(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str) -> None:
    deleted = await store.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")


async def _project_read(project) -> ProjectRead:
    style_reference_image_url = None
    if project.style_reference_image_file_id:
        media_file = await store.get_media_file(project.style_reference_image_file_id)
        style_reference_image_url = media_file.url if media_file else None
    return ProjectRead.model_validate(project).model_copy(
        update={"style_reference_image_url": style_reference_image_url}
    )
