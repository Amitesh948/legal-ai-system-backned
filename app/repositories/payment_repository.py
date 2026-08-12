from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """
    Repository for Payment model.
    Inherits basic CRUD operations from BaseRepository.
    """
    
    async def get_by_razorpay_order_id(self, db: AsyncSession, order_id: str) -> Optional[Payment]:
        """Fetch a payment by its Razorpay Order ID."""
        stmt = select(self.model).where(self.model.razorpay_order_id == order_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_case_id(self, db: AsyncSession, case_id: UUID) -> List[Payment]:
        """Fetch all payments for a specific case."""
        stmt = select(self.model).where(self.model.case_id == case_id).order_by(self.model.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_client_id(self, db: AsyncSession, client_id: UUID) -> List[Payment]:
        """Fetch all payments for a specific client."""
        stmt = select(self.model).where(self.model.client_id == client_id).order_by(self.model.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

payment_repo = PaymentRepository(Payment)
