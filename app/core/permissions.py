"""
Legal AI System - Role-Based Access Control (RBAC)
====================================================
Permission checking dependencies for FastAPI routes.
"""

import enum
from functools import wraps
from typing import List

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user_token


class UserRole(str, enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"
    ADVOCATE = "advocate"
    CLIENT = "client"


def require_roles(allowed_roles: List[UserRole]):
    """
    FastAPI dependency factory: restricts endpoint access to specific roles.
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
        async def admin_route():
            ...
    
    Or as a parameter dependency:
        @router.get("/advocates")
        async def advocate_route(
            token: dict = Depends(require_roles([UserRole.ADMIN, UserRole.ADVOCATE]))
        ):
            user_id = token["sub"]
    """
    async def role_checker(
        token_data: dict = Depends(get_current_user_token),
    ) -> dict:
        user_role = token_data.get("role")
        if user_role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return token_data

    return role_checker


# --- Convenience Dependencies ---
require_admin = require_roles([UserRole.ADMIN])
require_advocate = require_roles([UserRole.ADMIN, UserRole.ADVOCATE])
require_client = require_roles([UserRole.ADMIN, UserRole.CLIENT])
require_any_authenticated = require_roles([UserRole.ADMIN, UserRole.ADVOCATE, UserRole.CLIENT])
