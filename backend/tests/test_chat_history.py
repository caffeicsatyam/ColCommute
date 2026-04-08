from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from colcommute.db.models import ChatMessage, ChatSession, User
from services.auth_service import create_access_token

def _auth_header(user: User) -> dict[str, str]:
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_chat_history_empty(client: TestClient, db: Session) -> None:
    user = User(external_user_id="auth_u1", email="u1@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    res = client.get("/chat/history", params={"session_id": "s1"}, headers=_auth_header(user))
    assert res.status_code == 200
    body = res.json()
    assert body["session_id"] == "s1"
    assert body["messages"] == []


def test_chat_history_returns_messages_in_order(client: TestClient, db: Session) -> None:
    user = User(external_user_id="auth_u1", email="u1@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    sess = ChatSession(user_id=user.id, client_session_id="s1")
    db.add(sess)
    db.flush()

    db.add(ChatMessage(session_id=sess.id, role="user", content="hi"))
    db.add(ChatMessage(session_id=sess.id, role="assistant", content="hello"))
    db.commit()

    res = client.get("/chat/history", params={"session_id": "s1"}, headers=_auth_header(user))
    assert res.status_code == 200
    body = res.json()
    assert [m["role"] for m in body["messages"]] == ["user", "assistant"]
    assert [m["content"] for m in body["messages"]] == ["hi", "hello"]

