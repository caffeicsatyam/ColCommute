from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from colcommute.db.models import User
from colcommute.db.models import User
from services.auth_service import hash_password

def test_signup_creates_user_and_returns_token(client: TestClient) -> None:
    response = client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "user@example.com"
    assert body["access_token"]


def test_signup_rejects_duplicate_email(client: TestClient) -> None:
    first = client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )
    second = client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Email is already registered."


def test_login_returns_token_for_valid_credentials(
    client: TestClient, db: Session
) -> None:
    db.add(
        User(
            external_user_id="auth_existing_user",
            email="user@example.com",
            password_hash=hash_password("password123"),
        )
    )
    db.commit()

    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "user@example.com"
    assert body["access_token"]


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_auth_me_returns_current_user(client: TestClient) -> None:
    signup = client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "password123"},
    )

    token = signup.json()["access_token"]
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert response.json()["external_user_id"].startswith("auth_")
