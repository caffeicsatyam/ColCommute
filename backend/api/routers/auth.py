"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserResponse
from services.auth_service import (
    AuthenticationError,
    UserAlreadyExistsError,
    authenticate_user,
    create_access_token,
    signup_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Email is already registered.",
            "content": {
                "application/json": {
                    "example": {"detail": "Email is already registered."}
                }
            },
        }
    },
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> dict:
    try:
        user = signup_user(db, email=payload.email, password=payload.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user,
        "message": "User created successfully",
    }


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid email or password.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password."}
                }
            },
        }
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    try:
        user = authenticate_user(db, email=payload.email, password=payload.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user,
    }


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired token."}
                }
            },
        }
    },
)
def read_current_user(user=Depends(get_current_user)) -> UserResponse:
    return user
