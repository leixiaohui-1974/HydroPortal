"""Authentication router — login, token, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import DEMO_USERS, get_current_user, issue_token
from backend.models import LoginRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate with username/password and receive a JWT."""
    user = DEMO_USERS.get(req.username)
    if user is None or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = issue_token(req.username, user["role"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserInfo)
async def me(user: dict = Depends(get_current_user)):
    """Return the current authenticated user's info."""
    return UserInfo(
        username=user["username"],
        role=user["role"],
        display_name=user["display_name"],
    )
