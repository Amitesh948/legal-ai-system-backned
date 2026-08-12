from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """
    Repository for AuditLog model.
    Inherits basic CRUD operations from BaseRepository.
    """
    
    async def get_logs_paginated(
        self, db: AsyncSession, skip: int = 0, limit: int = 50
    ) -> List[AuditLog]:
        """Fetch audit logs with pagination and eager-loaded user info."""
        # Using selectinload to eagerly fetch the associated user for display purposes
        stmt = (
            select(self.model)
            .options(selectinload(self.model.user))
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

audit_log_repo = AuditLogRepository(AuditLog)
