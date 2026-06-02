from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_mcp_token,
    create_refresh_token,
    hash_password,
    hash_token,
    refresh_token_expires_at,
    verify_password,
)
from app.schemas.auth import (
    AuthTokenResponse,
    LogoutRequest,
    McpTokenCreate,
    McpTokenCreateResponse,
    McpTokenRead,
    RefreshTokenRequest,
    UserLogin,
    UserRead,
    UserRegister,
)
from app.services.database_store import store
from app.services.memory_store import UserRecord

router = APIRouter()


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
async def register(payload: UserRegister) -> AuthTokenResponse:
    if await store.get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="Email is already registered")
    if await store.get_user_by_username(payload.username):
        raise HTTPException(status_code=409, detail="Username is already registered")

    user = await store.create_user(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
    )
    return await _issue_tokens(user)


@router.post("/login", response_model=AuthTokenResponse)
async def login(payload: UserLogin) -> AuthTokenResponse:
    user = await store.get_user_by_login(payload.login)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid login or password")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="User is not active")

    await store.touch_user_login(user.id)
    refreshed_user = await store.get_user(user.id)
    return await _issue_tokens(refreshed_user or user)


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh(payload: RefreshTokenRequest) -> AuthTokenResponse:
    session = await store.get_user_session_by_hash(hash_token(payload.refresh_token))
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await store.get_user(session.user_id)
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="Invalid or inactive user")

    await store.revoke_user_session(session.id)
    return await _issue_tokens(user)


@router.post("/logout")
async def logout(payload: LogoutRequest) -> dict[str, str]:
    session = await store.get_user_session_by_hash(hash_token(payload.refresh_token))
    if session:
        await store.revoke_user_session(session.id)
    return {"status": "ok"}


@router.get("/me", response_model=UserRead)
async def me(current_user: UserRecord = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/mcp-tokens", response_model=McpTokenCreateResponse, status_code=201)
async def create_mcp_access_token(
    payload: McpTokenCreate,
    current_user: UserRecord = Depends(get_current_user),
) -> McpTokenCreateResponse:
    token = create_mcp_token()
    record = await store.create_user_mcp_token(
        user_id=current_user.id,
        name=payload.name,
        token_hash=hash_token(token),
    )
    return McpTokenCreateResponse(
        id=record.id,
        name=record.name,
        token=token,
        created_at=record.created_at,
    )


@router.get("/mcp-tokens", response_model=list[McpTokenRead])
async def list_mcp_access_tokens(
    current_user: UserRecord = Depends(get_current_user),
) -> list[McpTokenRead]:
    return [
        McpTokenRead(
            id=token.id,
            name=token.name,
            created_at=token.created_at,
            last_used_at=token.last_used_at,
        )
        for token in await store.list_user_mcp_tokens(current_user.id)
    ]


@router.delete("/mcp-tokens/{token_id}", status_code=204)
async def revoke_mcp_access_token(
    token_id: str,
    current_user: UserRecord = Depends(get_current_user),
) -> None:
    revoked = await store.revoke_user_mcp_token(token_id, user_id=current_user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="MCP token not found")


async def _issue_tokens(user: UserRecord) -> AuthTokenResponse:
    refresh_token = create_refresh_token()
    await store.create_user_session(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=refresh_token_expires_at().replace(tzinfo=None),
    )
    return AuthTokenResponse(
        access_token=create_access_token(subject=user.id),
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )
