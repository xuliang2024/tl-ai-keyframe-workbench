from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: str = "other"
    description: str = ""
    default_prompt: str = ""
    tags: list[str] = Field(default_factory=list)
    image_file_id: str | None = None
    sort_order: int = 0


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: str | None = None
    description: str | None = None
    default_prompt: str | None = None
    tags: list[str] | None = None
    image_file_id: str | None = None
    sort_order: int | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    owner_user_id: str | None = None
    type: str
    name: str
    description: str
    default_prompt: str
    tags: list[str]
    image_file_id: str | None
    image_url: str | None = None
    sort_order: int
    created_at: str
    updated_at: str


class AssetList(BaseModel):
    project_id: str
    items: list[AssetRead]
