from fastapi import APIRouter

from app.api.v1 import assets, frames, generation_tasks, health, mcp_docs, media, projects, scripts, video_segments
from app.mcp.streamable_http_handler import router as mcp_http_router

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(scripts.router, tags=["scripts"])
api_router.include_router(assets.router, tags=["assets"])
api_router.include_router(frames.router, tags=["frames"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(generation_tasks.router, prefix="/generation-tasks", tags=["generation-tasks"])
api_router.include_router(video_segments.router, tags=["video-segments"])
api_router.include_router(mcp_docs.router)
api_router.include_router(mcp_http_router)
