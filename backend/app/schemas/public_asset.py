from pydantic import BaseModel, ConfigDict, Field

from app.schemas.asset import AssetRead


class PublicAssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: str = "other"
    description: str = ""
    default_prompt: str = ""
    tags: list[str] = Field(default_factory=list)
    image_file_id: str | None = None
    sort_order: int = 0
    status: str = "active"


class PublicAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    name: str
    description: str
    default_prompt: str
    tags: list[str]
    image_file_id: str | None
    image_url: str | None = None
    sort_order: int
    status: str
    created_at: str
    updated_at: str


class PublicAssetImageCreate(BaseModel):
    media_file_id: str
    role: str = "reference"
    title: str = ""
    description: str = ""
    prompt: str = ""
    scene_prompt: str = ""
    angle: str = ""
    tags: list[str] = Field(default_factory=list)
    is_primary: bool = False
    sort_order: int = 0
    source_type: str = "uploaded"
    generation_task_id: str | None = None
    generation_prompt: str = ""


class PublicAssetImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_asset_id: str
    media_file_id: str
    image_url: str | None = None
    role: str
    title: str
    description: str
    prompt: str
    scene_prompt: str
    angle: str
    tags: list[str]
    is_primary: bool
    sort_order: int
    source_type: str = "uploaded"
    generation_task_id: str | None = None
    generation_prompt: str = ""
    created_by_user_id: str | None = None
    created_by_name: str | None = None
    created_at: str
    updated_at: str


class PublicAssetImageList(BaseModel):
    public_asset_id: str
    items: list[PublicAssetImageRead]


class PublicAssetList(BaseModel):
    items: list[PublicAssetRead]


class PublicAssetImportCreate(BaseModel):
    public_asset_ids: list[str] = Field(min_length=1)
    copy_media: bool = True


class PublicAssetImportError(BaseModel):
    public_asset_id: str
    detail: str


class PublicAssetImportResult(BaseModel):
    project_id: str
    items: list[AssetRead]
    errors: list[PublicAssetImportError] = Field(default_factory=list)
