from pydantic import BaseModel, ConfigDict, Field


class FrameCreate(BaseModel):
    summary: str = ""
    order_index: int | None = Field(default=None, ge=1)
    duration_ms: int = Field(default=3000, ge=500)
    current_prompt: str = ""


class FrameUpdate(BaseModel):
    summary: str | None = None
    duration_ms: int | None = Field(default=None, ge=500)
    people: str | None = None
    dialogue: str | None = None
    action: str | None = None
    emotion: str | None = None
    note: str | None = None
    current_prompt: str | None = None
    selected_version_id: str | None = None


class FrameVersionCreate(BaseModel):
    image_file_id: str | None = None
    generation_task_id: str | None = None
    prompt: str = ""
    note: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)
    select: bool = True


class FrameVersionSelect(BaseModel):
    version_id: str


class FrameVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    frame_id: str
    owner_user_id: str | None = None
    version_no: int
    image_file_id: str | None
    image_url: str | None = None
    generation_task_id: str | None
    prompt: str
    note: str
    metadata: dict[str, object]
    created_at: str


class FrameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    owner_user_id: str | None = None
    order_index: int
    summary: str
    duration_ms: int
    people: str
    dialogue: str
    action: str
    emotion: str
    note: str
    current_prompt: str
    selected_version_id: str | None
    versions: list[FrameVersionRead] = Field(default_factory=list)
    created_at: str
    updated_at: str


class FrameList(BaseModel):
    project_id: str
    items: list[FrameRead]
