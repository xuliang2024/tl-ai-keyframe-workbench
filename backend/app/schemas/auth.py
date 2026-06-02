import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


USERNAME_RE = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]{2,79}$")


class UserRegister(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=120)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("email must be valid")
        return normalized

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not USERNAME_RE.match(normalized):
            raise ValueError("username may contain letters, numbers, dots, dashes, and underscores")
        return normalized

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str) -> str:
        return value.strip()


class UserLogin(BaseModel):
    login: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("login")
    @classmethod
    def normalize_login(cls, value: str) -> str:
        return value.strip().lower()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class McpTokenCreate(BaseModel):
    name: str = Field(default="MCP token", min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class McpTokenRead(BaseModel):
    id: str
    name: str
    created_at: str
    last_used_at: str | None


class McpTokenCreateResponse(BaseModel):
    id: str
    name: str
    token: str
    created_at: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    display_name: str
    avatar_url: str | None
    status: str
    created_at: str
    updated_at: str
    last_login_at: str | None


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead
