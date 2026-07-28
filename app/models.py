from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    user_id: str | None = None
    context: str | None = None


class SourceChunk(BaseModel):
    text: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    confidence: float
    elapsed_ms: float
    sources: list[SourceChunk]

class BitrixWebhookRequest(BaseModel):
    event: str | None = None
    data: dict[str, Any]


class BitrixWebhookResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str