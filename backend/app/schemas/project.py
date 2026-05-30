from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    aspect_ratio: str = "16:9"


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    aspect_ratio: str | None = None
    status: str | None = None
    style_prompt: str | None = None
    style_reference_image_file_id: str | None = None
    auto_apply_style_prompt: bool | None = None
    auto_apply_style_reference: bool | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    aspect_ratio: str
    status: str
    style_prompt: str = ""
    style_reference_image_file_id: str | None = None
    style_reference_image_url: str | None = None
    auto_apply_style_prompt: bool = False
    auto_apply_style_reference: bool = False
    created_at: str
    updated_at: str


class ProjectList(BaseModel):
    items: list[ProjectRead]
