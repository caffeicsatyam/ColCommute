"""Authentication helpers for FastAPI endpoints."""

from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from colcommute.db.models import User

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = int(os.environ.get("PASSWORD_HASH_ITERATIONS", "390000"))
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)


class UserAlreadyExistsError(ValueError):
    """Raised when signup attempts to reuse an email."""


class AuthenticationError(ValueError):
    """Raised when login credentials are invalid."""


class TokenValidationError(ValueError):
    """Raised when a bearer token is missing or invalid."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _jwt_secret() -> str:
    return (
        os.environ.get("JWT_SECRET_KEY")
        or os.environ.get("SECRET_KEY")
        or "change-me-in-production-with-32-bytes"
    )


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"{PASSWORD_ALGORITHM}"
        f"${PASSWORD_HASH_ITERATIONS}"
        f"${salt.hex()}"
        f"${digest.hex()}"
    )


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False

    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", maxsplit=3)
    except ValueError:
        return False

    if algorithm != PASSWORD_ALGORITHM:
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return hmac.compare_digest(computed.hex(), digest_hex)


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user.id),
        "external_user_id": user.external_user_id,
        "email": user.email,
        "exp": expires_at,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def signup_user(session: Session, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    existing = session.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise UserAlreadyExistsError("Email is already registered.")

    user = User(
        external_user_id=f"auth_{uuid.uuid4().hex}",
        email=normalized_email,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    user = session.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")
    return user


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenValidationError("Invalid or expired token.") from exc


def get_user_from_token(session: Session, token: str) -> User:
    payload = decode_access_token(token)
    external_user_id = payload.get("external_user_id")
    if not external_user_id:
        raise TokenValidationError("Invalid or expired token.")

    user = session.scalar(select(User).where(User.external_user_id == external_user_id))
    if user is None:
        raise TokenValidationError("Invalid or expired token.")
    return user
