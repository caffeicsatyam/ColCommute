"""Single chat endpoint that streams via SSE."""

from __future__ import annotations

import json
import re
import uuid
from functools import lru_cache
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageOut,
    ChatSessionsResponse,
    ChatSessionOut,
    ChatStreamRequest,
)
from colcommute.agent import root_agent
from colcommute.db.models.chat_message import ChatMessage
from colcommute.db.models.chat_session import ChatSession
from colcommute.db.session import session_scope

router = APIRouter(prefix="/chat", tags=["chat"])


@lru_cache(maxsize=1)
def _runner() -> Runner:
    session_service = InMemorySessionService()
    return Runner(app_name="colcommute", agent=root_agent, session_service=session_service)


def _content_text(content: types.Content | None) -> str:
    if not content or not content.parts:
        return ""
    chunks: list[str] = []
    for part in content.parts:
        text = getattr(part, "text", None)
        if isinstance(text, str) and text:
            chunks.append(text)
    return "\n".join(chunks)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _word_chunks(text: str) -> list[str]:
    # Preserve whitespace so the UI renders naturally while still streaming
    # in small "word-like" increments.
    return re.findall(r"\S+|\s+", text)


_UI_MARKER_RE = re.compile(r"\[\[UI:(?P<action>[a-z_]+):(?P<field>[a-z_]+)\]\]")


def _strip_ui_markers(text: str) -> str:
    # Markers are meant for the frontend; never show them in chat text.
    return _UI_MARKER_RE.sub("", text)


async def _ensure_session(*, runner: Runner, user_id: str, session_id: str) -> None:
    existing = await runner.session_service.get_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if existing is None:
        await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )


@router.post("/stream")
async def chat_stream(
    payload: ChatStreamRequest,
    user=Depends(get_current_user),
):
    runner = _runner()

    user_uuid = getattr(user, "id")
    user_id = str(user_uuid)
    session_id = payload.session_id or f"user:{user_id}"
    invocation_id = str(uuid.uuid4())

    new_message = types.Content(role="user", parts=[types.Part(text=payload.message)])

    async def event_gen() -> AsyncGenerator[str, None]:
        # Initial metadata (useful for the UI)
        yield _sse({"type": "meta", "session_id": session_id})

        await _ensure_session(runner=runner, user_id=user_id, session_id=session_id)

        # Persist user message + ensure chat session exists.
        try:
            with session_scope() as db:
                chat_session = db.execute(
                    select(ChatSession).where(
                        ChatSession.user_id == user_uuid,
                        ChatSession.client_session_id == session_id,
                    )
                ).scalar_one_or_none()
                if chat_session is None:
                    chat_session = ChatSession(user_id=user_uuid, client_session_id=session_id)
                    db.add(chat_session)
                    db.flush()

                db.add(ChatMessage(session_id=chat_session.id, role="user", content=payload.message))
        except Exception:
            # Don't fail chat streaming if DB is temporarily unavailable.
            pass

        last_text = ""
        last_clean_text = ""
        emitted_markers: set[str] = set()
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            invocation_id=invocation_id,
            new_message=new_message,
        ):
            # ADK emits events with content; for a basic chat UI we only stream text.
            text = _content_text(getattr(event, "content", None))
            if not text:
                continue

            # Emit UI events based on explicit agent markers.
            for m in _UI_MARKER_RE.finditer(text):
                marker_key = m.group(0)
                if marker_key in emitted_markers:
                    continue
                emitted_markers.add(marker_key)
                yield _sse(
                    {
                        "type": "ui",
                        "action": m.group("action"),
                        "field": m.group("field"),
                    }
                )

            clean_text = _strip_ui_markers(text)

            # Some events repeat the full text; stream only the delta.
            if clean_text.startswith(last_clean_text):
                delta = clean_text[len(last_clean_text) :]
            else:
                delta = clean_text
            last_text = text
            last_clean_text = clean_text

            if delta:
                for chunk in _word_chunks(delta):
                    if chunk:
                        yield _sse({"type": "delta", "text": chunk})

        # Persist assistant final text.
        try:
            final_text = last_clean_text.strip()
            if final_text:
                with session_scope() as db:
                    chat_session = db.execute(
                        select(ChatSession).where(
                            ChatSession.user_id == user_uuid,
                            ChatSession.client_session_id == session_id,
                        )
                    ).scalar_one_or_none()
                    if chat_session is None:
                        chat_session = ChatSession(user_id=user_uuid, client_session_id=session_id)
                        db.add(chat_session)
                        db.flush()
                    db.add(ChatMessage(session_id=chat_session.id, role="assistant", content=final_text))
        except Exception:
            pass

        yield _sse({"type": "done"})

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/history", response_model=ChatHistoryResponse)
def chat_history(
    session_id: str = Query(min_length=1, max_length=128),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_uuid = getattr(user, "id")
    chat_session = db.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_uuid,
            ChatSession.client_session_id == session_id,
        )
    ).scalar_one_or_none()
    if chat_session is None:
        return ChatHistoryResponse(session_id=session_id, messages=[])

    rows = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session.id)
        .order_by(ChatMessage.created_at)
    ).scalars()

    messages = [
        ChatMessageOut(
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in rows
    ]
    return ChatHistoryResponse(session_id=session_id, messages=messages)


@router.get("/sessions", response_model=ChatSessionsResponse)
def list_chat_sessions(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_uuid = getattr(user, "id")
    rows = db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_uuid)
        .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
    ).scalars()

    sessions: list[ChatSessionOut] = []
    for s in rows:
        last = db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == s.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        sessions.append(
            ChatSessionOut(
                session_id=s.client_session_id,
                updated_at=s.updated_at.isoformat(),
                last_message=(last.content if last else None),
            )
        )
    return ChatSessionsResponse(sessions=sessions)
