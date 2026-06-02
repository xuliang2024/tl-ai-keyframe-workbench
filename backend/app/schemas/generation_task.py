from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


ImageTaskType = Literal["text_to_image", "image_to_image", "image_edit"]
VideoTaskType = Literal["text_to_video", "frames_to_video"]
GenerationTaskType = ImageTaskType | VideoTaskType
GenerationTaskStatus = Literal["queued", "running", "succeeded", "failed", "canceled"]
ImageResponseFormat = Literal["url", "b64_json"]
ImageType = Literal["style", "character", "scene", "prop", "keyframe"]
GenerationTargetType = Literal["public_asset_gallery", "project_asset", "keyframe", "video"]


class GenerationTaskTarget(BaseModel):
    type: GenerationTargetType
    id: str | None = None
    public_asset_id: str | None = None
    title: str = ""
    role: str = "generated"
    angle: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class GenerationTaskReference(BaseModel):
    type: str
    id: str | None = None
    url: str | None = None
    title: str = ""


class GenerationTaskCreate(BaseModel):
    task_type: GenerationTaskType | None = None
    prompt: str = Field(..., min_length=1)
    aspect_ratio: str = "16:9"
    image: str | list[str] | None = None
    size: str | None = None
    watermark: bool = False
    project_id: str | None = None
    frame_id: str | None = None
    asset_ids: list[str] | None = None
    auto_apply_asset_references: bool = True
    image_type: ImageType | None = None
    target: GenerationTaskTarget | None = None
    references: list[GenerationTaskReference] = Field(default_factory=list)

    @field_validator("prompt", "aspect_ratio")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("image")
    @classmethod
    def strip_images(cls, value: str | list[str] | None) -> str | list[str] | None:
        if isinstance(value, str):
            return value.strip() or None
        if isinstance(value, list):
            return [item.strip() for item in value if item.strip()]
        return value

    @field_validator("frame_id", "project_id")
    @classmethod
    def strip_optional_id(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @field_validator("asset_ids")
    @classmethod
    def strip_asset_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [item.strip() for item in value if item.strip()]


class GeneratedImage(BaseModel):
    url: str | None = None
    b64_json: str | None = None
    size: str | None = None
    media_file_id: str | None = None
    object_key: str | None = None
    error: dict[str, Any] | None = None


class GenerationTaskResponse(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    owner_user_id: str | None = None
    status: GenerationTaskStatus
    task_type: GenerationTaskType
    provider: str = "apiz"
    model_name: str
    prompt: str
    aspect_ratio: str
    size: str
    target_type: str | None = None
    target_id: str | None = None
    target_payload: dict[str, Any] = Field(default_factory=dict)
    reference_payload: list[dict[str, Any]] = Field(default_factory=list)
    images: list[GeneratedImage] = Field(default_factory=list)
    usage: dict[str, Any] | None = None
    response_payload: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class GenerationTaskList(BaseModel):
    items: list[GenerationTaskResponse]
