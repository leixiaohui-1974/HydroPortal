"""Role-based authorization middleware for HydroPortal."""

from __future__ import annotations

from typing import Sequence

from fastapi import Depends, HTTPException, status

from backend.deps import get_current_user


def require_role(allowed_roles: Sequence[str]):
    """Return a FastAPI dependency that enforces role-based access.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role(["admin"]))])
        async def admin_endpoint():
            ...

    Or inject the user directly::

        @router.get("/ops")
        async def ops_endpoint(user=Depends(require_role(["admin", "operator"]))):
            return {"user": user}
    """

    async def _check_role(
        user: dict[str, str] = Depends(get_current_user),
    ) -> dict[str, str]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {', '.join(allowed_roles)}",
            )
        return user

    return _check_role
