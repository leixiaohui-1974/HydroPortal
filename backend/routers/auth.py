"""Authentication router — login, token, current user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.deps import (
    get_current_user,
    get_demo_users,
    issue_token,
    verify_password,
)
from backend.models import LoginRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate with username/password and receive a JWT."""
    demo_users = get_demo_users()
    if not demo_users:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password login is disabled. Enable HYDROPORTAL_DEMO_AUTH_ENABLED in dev/demo mode.",
        )
    user = demo_users.get(req.username)
    if user is None or not verify_password(req.password, user["password"]):
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
