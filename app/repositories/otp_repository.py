from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.otp import OTPVerification
from app.repositories.base import BaseRepository

class OTPRepository(BaseRepository[OTPVerification]):
    def __init__(self):
        super().__init__(OTPVerification)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[OTPVerification]:
        query = select(self.model).where(self.model.email == email).order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().first()

otp_repository = OTPRepository()
