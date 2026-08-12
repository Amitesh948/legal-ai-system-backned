"""
Legal AI System - User Repository
===================================
Database access operations specifically for the User model.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User-specific database operations."""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Fetch a user by their email address."""
        query = select(self.model).where(self.model.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Singleton instance
user_repository = UserRepository()
