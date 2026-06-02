from pydantic import BaseModel, ConfigDict


class ScriptUpdate(BaseModel):
    content: str = ""


class ScriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: str
    owner_user_id: str | None = None
    content: str
    updated_at: str
