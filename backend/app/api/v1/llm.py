from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.core.config import settings
from app.integrations.llm import LLMClient, LLMError

router = APIRouter()


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMChatRequest(BaseModel):
    prompt: str | None = None
    messages: list[LLMMessage] = Field(default_factory=list)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_prompt_or_messages(self) -> "LLMChatRequest":
        if not self.prompt and not self.messages:
            raise ValueError("prompt or messages is required")
        return self


class LLMChatResponse(BaseModel):
    model: str
    content: str
    raw_response: dict


@router.get("/config")
async def get_llm_config() -> dict[str, object]:
    return {
        "configured": bool(settings.llm_api_key),
        "base_url": settings.llm_base_url,
        "model": settings.llm_model,
    }


@router.post("/chat", response_model=LLMChatResponse)
async def chat(payload: LLMChatRequest) -> LLMChatResponse:
    messages = [message.model_dump() for message in payload.messages]
    if payload.prompt:
        messages.append({"role": "user", "content": payload.prompt})

    client = LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    try:
        response = await client.chat(
            messages=messages,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return LLMChatResponse(
        model=settings.llm_model,
        content=client.extract_text(response),
        raw_response=response,
    )
