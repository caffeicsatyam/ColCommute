"""Chat (SSE) request models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatStreamRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)
    session_id: str | None = Field(
        default=None,
        description="Optional conversation session id. If omitted, a per-user default is used.",
    )


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageOut]


class ChatSessionOut(BaseModel):
    session_id: str
    updated_at: str
    last_message: str | None = None


class ChatSessionsResponse(BaseModel):
    sessions: list[ChatSessionOut]

