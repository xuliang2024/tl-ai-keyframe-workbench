from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


MediaFileType = Literal["image", "video"]


class MediaUploadUrlCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    file_type: MediaFileType
    mime_type: str = Field(min_length=1, max_length=120)
    size_bytes: int | None = Field(default=None, gt=0)
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mime_type(self) -> "MediaUploadUrlCreate":
        if self.file_type == "image" and not self.mime_type.startswith("image/"):
            raise ValueError("mime_type must start with image/ for image uploads")
        if self.file_type == "video" and not self.mime_type.startswith("video/"):
            raise ValueError("mime_type must start with video/ for video uploads")
        return self


class MediaUploadUrlRead(BaseModel):
    media_file_id: str
    file_type: str
    bucket: str
    object_key: str
    upload_url: str
    upload_method: str = "PUT"
    upload_headers: dict[str, str]
    public_url: str
    expires_in: int


class MediaUploadComplete(BaseModel):
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    duration_ms: int | None = Field(default=None, ge=0)
    size_bytes: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MediaFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str | None
    file_type: str
    bucket: str
    object_key: str
    url: str
    mime_type: str
    width: int | None
    height: int | None
    duration_ms: int | None
    size_bytes: int | None
    metadata: dict[str, Any]
    status: str
    created_at: str
    updated_at: str
