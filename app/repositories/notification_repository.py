from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.models.notification import Notification
from app.repositories.base import BaseRepository

class NotificationRepository(BaseRepository[Notification]):
    def __init__(self):
        super().__init__(Notification)

    async def get_by_user(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> List[Notification]:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_unread_count(self, db: AsyncSession, user_id: UUID) -> int:
        query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id, 
            Notification.is_read == False
        )
        result = await db.execute(query)
        return result.scalar() or 0

    async def mark_as_read(self, db: AsyncSession, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        query = select(Notification).where(
            Notification.id == notification_id, 
            Notification.user_id == user_id
        )
        result = await db.execute(query)
        notification = result.scalars().first()
        
        if notification:
            notification.is_read = True
            await db.commit()
            await db.refresh(notification)
            return notification
        return None

    async def mark_all_as_read(self, db: AsyncSession, user_id: UUID) -> int:
        query = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount

notification_repository = NotificationRepository()
