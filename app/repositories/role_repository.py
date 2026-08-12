"""
Legal AI System - Role Repository
===================================
Database access operations specifically for the Role model.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Role-specific database operations."""

    def __init__(self):
        super().__init__(Role)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """Fetch a role by its name (e.g., 'admin', 'advocate', 'client')."""
        query = select(self.model).where(self.model.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Singleton instance
role_repository = RoleRepository()
